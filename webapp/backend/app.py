import json
import logging
import sqlite3
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["OPTIONS", "POST", "GET"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация базы данных
DATABASE = 'game.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Создание таблицы пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 0,
            max_clicks INTEGER DEFAULT 10,
            clicks_count INTEGER DEFAULT 10,
            click_power INTEGER DEFAULT 1000,
            hourly_income INTEGER DEFAULT 4570000,
            progress INTEGER DEFAULT 8450,
            max_progress INTEGER DEFAULT 8500,
            boost_active INTEGER DEFAULT 0,
            boost_end_time INTEGER DEFAULT 0,
            last_play_time INTEGER DEFAULT 0,
            upgrades TEXT DEFAULT '{}',
            friends TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Создание таблицы улучшений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS upgrades (
            upgrade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            base_cost INTEGER
        )
        ''')

        # Создание таблицы рефералов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT,
            referred_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users (user_id),
            FOREIGN KEY (referred_id) REFERENCES users (user_id)
        )
        ''')

        # Инициализация стандартных улучшений
        cursor.execute('SELECT COUNT(*) FROM upgrades')
        if cursor.fetchone()[0] == 0:
            default_upgrades = [
                ('Мощность клика', '+100 монет за клик', 100),
                ('Количество кликов', '+5 максимальных кликов', 200),
                ('Доход в час', '+1M монет в час', 500),
                ('Автоматическая добыча', '+0.5M монет в час', 1000)
            ]
            cursor.executemany(
                'INSERT INTO upgrades (name, description, base_cost) VALUES (?, ?, ?)',
                default_upgrades
            )

        db.commit()
        logger.info("Database initialized successfully")


@app.route('/api/user', methods=['POST'])
def create_or_get_user():
    try:
        data = request.json
        user_id = data.get('user_id')
        username = data.get('username')

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        db = get_db()
        cursor = db.cursor()

        # Проверяем существующего пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        # Если пользователь не существует, создаем нового
        if not user:
            # Проверяем реферальный код
            referrer_id = None
            if data.get('ref_code'):
                ref_code = data['ref_code'].split('_')[-1]
                cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (ref_code,))
                if cursor.fetchone():
                    referrer_id = ref_code

            # Создаем нового пользователя
            cursor.execute('''
            INSERT INTO users (user_id, username, coins, max_clicks, clicks_count, 
                               click_power, hourly_income, progress, max_progress)
            VALUES (?, ?, 0, 10, 10, 1000, 4570000, 8450, 8500)
            ''', (user_id, username))

            # Добавляем реферала
            if referrer_id:
                cursor.execute('''
                INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)
                ''', (referrer_id, user_id))

                # Награда рефереру
                cursor.execute('''
                UPDATE users SET coins = coins + 5000000
                WHERE user_id = ?
                ''', (referrer_id,))

            db.commit()
            logger.info(f"New user created: {user_id}")
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()

        # Обработка автоматического дохода
        process_auto_income(user)

        # Форматируем данные пользователя для ответа
        user_data = dict(user)
        user_data['upgrades'] = json.loads(user_data.get('upgrades', '{}'))
        user_data['friends'] = json.loads(user_data.get('friends', '[]'))

        return jsonify(user_data)
    except Exception as e:
        logger.error(f"Error in create_or_get_user: {str(e)}")
        return jsonify({'error': str(e)}), 500


def process_auto_income(user):
    """Обработка автоматического дохода при загрузке пользователя"""
    if not user['last_play_time']:
        return

    db = get_db()
    cursor = db.cursor()

    last_play = datetime.fromtimestamp(user['last_play_time'])
    time_passed = datetime.now() - last_play
    hours_passed = time_passed.total_seconds() / 3600

    # Рассчитываем доход от автоматической добычи
    upgrades = json.loads(user.get('upgrades', '{}'))
    auto_mine_level = upgrades.get('auto_mine', {}).get('level', 0)
    auto_income = user['hourly_income'] * (1 + auto_mine_level * 0.5) * hours_passed

    if auto_income > 0:
        cursor.execute('''
        UPDATE users 
        SET coins = coins + ?, 
            last_play_time = ?
        WHERE user_id = ?
        ''', (int(auto_income), int(time.time()), user['user_id']))
        db.commit()
        logger.info(f"Auto income added for {user['user_id']}: {int(auto_income)} coins")


@app.route('/api/click', methods=['POST'])
def handle_click():
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        db = get_db()
        cursor = db.cursor()

        # Получаем данные пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Проверяем доступные клики
        if user['clicks_count'] <= 0:
            return jsonify({'error': 'No clicks available'}), 400

        # Рассчитываем доход от клика
        boost_multiplier = 2 if user['boost_active'] and user['boost_end_time'] > time.time() else 1
        coins_earned = user['click_power'] * boost_multiplier

        # Обновляем данные пользователя
        cursor.execute('''
        UPDATE users 
        SET coins = coins + ?,
            clicks_count = clicks_count - 1,
            last_play_time = ?
        WHERE user_id = ?
        ''', (coins_earned, int(time.time()), user_id))
        db.commit()

        # Получаем обновленные данные
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        updated_user = cursor.fetchone()

        # Форматируем данные для ответа
        user_data = dict(updated_user)
        user_data['upgrades'] = json.loads(user_data.get('upgrades', '{}'))
        user_data['friends'] = json.loads(user_data.get('friends', '[]'))

        return jsonify({
            'success': True,
            'coins_earned': coins_earned,
            'user': user_data
        })
    except Exception as e:
        logger.error(f"Error in handle_click: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upgrade', methods=['POST'])
def handle_upgrade():
    try:
        data = request.json
        user_id = data.get('user_id')
        upgrade_type = data.get('type')

        if not user_id or not upgrade_type:
            return jsonify({'error': 'User ID and upgrade type required'}), 400

        db = get_db()
        cursor = db.cursor()

        # Получаем данные пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Получаем информацию об улучшении
        cursor.execute('SELECT * FROM upgrades WHERE upgrade_id = ?', (int(upgrade_type) + 1,))
        upgrade_info = cursor.fetchone()

        if not upgrade_info:
            return jsonify({'error': 'Upgrade not found'}), 404

        # Получаем текущие улучшения пользователя
        upgrades = json.loads(user.get('upgrades', '{}'))
        upgrade_data = upgrades.get(upgrade_type, {'level': 0, 'cost': upgrade_info['base_cost']})

        # Проверяем стоимость
        if user['coins'] < upgrade_data['cost']:
            return jsonify({
                'success': False,
                'error': 'Not enough coins',
                'required': upgrade_data['cost'],
                'current': user['coins']
            }), 400

        # Применяем улучшение
        new_level = upgrade_data['level'] + 1
        new_cost = int(upgrade_data['cost'] * 1.5)

        # Обновляем характеристики пользователя в зависимости от типа улучшения
        if upgrade_type == 'click_power':
            cursor.execute('''
            UPDATE users 
            SET click_power = click_power + 100
            WHERE user_id = ?
            ''', (user_id,))
        elif upgrade_type == 'clicks_capacity':
            cursor.execute('''
            UPDATE users 
            SET max_clicks = max_clicks + 5,
                clicks_count = max_clicks + 5
            WHERE user_id = ?
            ''', (user_id,))
        elif upgrade_type == 'hourly_income':
            cursor.execute('''
            UPDATE users 
            SET hourly_income = hourly_income + 1000000
            WHERE user_id = ?
            ''', (user_id,))
        # Для auto_mine не требуется немедленных изменений

        # Обновляем улучшение
        upgrade_data['level'] = new_level
        upgrade_data['cost'] = new_cost
        upgrades[upgrade_type] = upgrade_data

        # Обновляем данные пользователя
        cursor.execute('''
        UPDATE users 
        SET coins = coins - ?,
            upgrades = ?
        WHERE user_id = ?
        ''', (upgrade_data['cost'], json.dumps(upgrades), user_id))
        db.commit()

        # Получаем обновленные данные
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        updated_user = cursor.fetchone()

        # Форматируем данные для ответа
        user_data = dict(updated_user)
        user_data['upgrades'] = json.loads(user_data.get('upgrades', '{}'))
        user_data['friends'] = json.loads(user_data.get('friends', '[]'))

        return jsonify({
            'success': True,
            'user': user_data,
            'upgrade': upgrade_data
        })
    except Exception as e:
        logger.error(f"Error in handle_upgrade: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/boost', methods=['POST'])
def activate_boost():
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        db = get_db()
        cursor = db.cursor()

        # Получаем данные пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Проверяем, активен ли уже буст
        if user['boost_active'] and user['boost_end_time'] > time.time():
            return jsonify({
                'success': False,
                'error': 'Boost already active'
            }), 400

        # Активируем буст на 30 секунд
        boost_end_time = int(time.time()) + 30

        cursor.execute('''
        UPDATE users 
        SET boost_active = 1,
            boost_end_time = ?
        WHERE user_id = ?
        ''', (boost_end_time, user_id))
        db.commit()

        return jsonify({
            'success': True,
            'boost_end_time': boost_end_time
        })
    except Exception as e:
        logger.error(f"Error in activate_boost: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/friends', methods=['POST'])
def get_friends():
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        db = get_db()
        cursor = db.cursor()

        # Получаем друзей пользователя (рефералов)
        cursor.execute('''
        SELECT u.user_id, u.username, u.coins, u.progress
        FROM referrals r
        JOIN users u ON r.referred_id = u.user_id
        WHERE r.referrer_id = ?
        ORDER BY u.coins DESC
        LIMIT 10
        ''', (user_id,))

        friends = [
            {
                'user_id': row['user_id'],
                'username': row['username'],
                'coins': row['coins'],
                'progress': row['progress']
            }
            for row in cursor.fetchall()
        ]

        # Получаем данные самого пользователя для лидерборда
        cursor.execute('''
        SELECT user_id, username, coins, progress
        FROM users 
        WHERE user_id = ?
        ''', (user_id,))
        user_row = cursor.fetchone()

        if user_row:
            user_data = {
                'user_id': user_row['user_id'],
                'username': user_row['username'],
                'coins': user_row['coins'],
                'progress': user_row['progress']
            }
            friends.insert(0, user_data)  # Добавляем пользователя в начало списка

        return jsonify({
            'success': True,
            'friends': friends
        })
    except Exception as e:
        logger.error(f"Error in get_friends: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/recover_clicks', methods=['POST'])
def recover_clicks():
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID required'}), 400

        db = get_db()
        cursor = db.cursor()

        # Восстанавливаем клики до максимума
        cursor.execute('''
        UPDATE users 
        SET clicks_count = max_clicks
        WHERE user_id = ?
        ''', (user_id,))
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Clicks recovered'
        })
    except Exception as e:
        logger.error(f"Error in recover_clicks: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    response = jsonify({'message': 'Preflight check passed'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)