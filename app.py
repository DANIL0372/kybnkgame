import sys
from flask import Flask, send_from_directory, jsonify, request, render_template
import sqlite3
import datetime
import os
import json
import random
from datetime import datetime, timedelta

app = Flask(__name__)

# Конфигурация
CONFIG = {
    'admin_password': 'DnK2025',
    'version': '2.1'
}

# ПРАВИЛЬНЫЙ путь для PythonAnywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_DB_PATH = os.path.join(BASE_DIR, 'kybnk_game.db')

# Список фейковых никнеймов (20 штук)
FAKE_USERNAMES = [
    "Константин", "GGD", "Свага", "DANISIMO", "Алинка",
    "Batt Bratt", "дишка", "Dearbornn", "Ванёчек", "Машка",
    "Denzl", "Валерия В", "OLESYAO", "kkk", "nellisaaaa",
    "No name", "Ali", "Карен", "OG", "2k17"
]

# Глобальная переменная для хранения текущего топа
current_top_players = []
last_top_update = datetime.now()

print(f"✅ ЗАГРУЖЕН ПРАВИЛЬНЫЙ APP.PY из: {os.path.abspath(__file__)}")
print(f"✅ База данных будет создана по пути: {NEW_DB_PATH}")
print(f"✅ App.py загружен из: {os.path.abspath(__file__)}", file=sys.stderr)
print(f"✅ Рабочая директория: {os.getcwd()}", file=sys.stderr)
print(f"✅ Templates существует: {os.path.exists('templates')}", file=sys.stderr)
print(f"✅ index.html существует: {os.path.exists('templates/index.html')}", file=sys.stderr)

def ensure_database():
    """Убеждаемся что база данных существует и имеет правильную структуру"""
    try:
        db_path = NEW_DB_PATH
        print(f"🔍 Проверяем базу данных: {db_path}")
        print(f"📁 Файл существует: {os.path.exists(db_path)}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Создаем таблицу если её нет
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                level_name TEXT DEFAULT 'Новичок 🟢',
                discount INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                total_earned INTEGER DEFAULT 0,
                referrals INTEGER DEFAULT 0,
                passive_income REAL DEFAULT 0,
                upgrades TEXT DEFAULT '{"click_power":1,"passive":0,"autoclick":0,"energy_limit":0}',
                bonuses TEXT DEFAULT '{"kybnk_show":false,"kybnk_shop":false}',
                energy INTEGER DEFAULT 100,
                max_energy INTEGER DEFAULT 100,
                last_energy_update INTEGER,
                last_passive_claim INTEGER,
                boost TEXT DEFAULT '{"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1}',
                theme TEXT DEFAULT 'dark',  -- ДОБАВЛЕНО: поле для темы
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Проверяем структуру
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("✅ Структура таблицы users:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        conn.commit()
        conn.close()
        print("✅ База данных проверена/создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания базы: {e}")
        return False

# Убеждаемся что база существует при запуске
ensure_database()

@app.route('/')
def home():
    print("🏠 Home route accessed - НОВАЯ ВЕРСИЯ")
    return render_template('index.html', version='2.1')

@app.route('/webapp')
def webapp():
    return render_template('index.html', version='2.1')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# API для работы с пользователями
@app.route('/api/user/<user_id>', methods=['GET', 'POST'])
def api_user(user_id):
    """API для получения и обновления данных пользователя"""
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if request.method == 'GET':
            # ... существующий код ...

            if user:
                user_dict = dict(user)
                # Преобразуем JSON поля
                for field in ['upgrades', 'bonuses', 'boost']:
                    if user_dict.get(field):
                        try:
                            user_dict[field] = json.loads(user_dict[field])
                        except:
                            user_dict[field] = {}

                conn.close()
                return jsonify(user_dict)
            # ... остальной код ...

        elif request.method == 'POST':
            # Обновляем или создаем данные пользователя
            data = request.json

            # Проверяем существует ли пользователь
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            existing_user = cursor.fetchone()

            # Подготавливаем данные для вставки/обновления
            # Подготавливаем данные для вставки/обновления
            insert_data = {
                'user_id': user_id,
                'username': data.get('username', 'Web User'),
                'balance': data.get('balance', 0),
                'level': data.get('level', 1),
                'level_name': data.get('level_name', 'Новичок 🟢'),
                'discount': data.get('discount', 0),
                'clicks': data.get('clicks', 0),
                'total_earned': data.get('total_earned', 0),
                'referrals': data.get('referrals', 0),
                'passive_income': data.get('passive_income', 0),
                'energy': data.get('energy', 100),
                'max_energy': data.get('max_energy', 100),
                'last_energy_update': data.get('last_energy_update', int(datetime.datetime.now().timestamp() * 1000)),
                'last_passive_claim': data.get('last_passive_claim', int(datetime.datetime.now().timestamp() * 1000)),
                'upgrades': json.dumps(data.get('upgrades', {"click_power":1,"passive":0,"autoclick":0,"energy_limit":0})),
                'bonuses': json.dumps(data.get('bonuses', {"kybnk_show":false,"kybnk_shop":false})),
                'boost': json.dumps(data.get('boost', {"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1})),
                'theme': data.get('theme', 'dark')  # ДОБАВЛЕНО: сохранение темы
            }

            if existing_user:
                # ОБНОВЛЯЕМ ВСЕ ПОЛЯ полностью
                updates = []
                values = []
                for key, value in insert_data.items():
                    if key != 'user_id':
                        updates.append(f"{key} = ?")
                        values.append(value)
                values.append(user_id)

                query = f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
                cursor.execute(query, values)
                action = "updated"
            else:
                # Создаем нового пользователя
                columns = ', '.join(insert_data.keys())
                placeholders = ', '.join(['?'] * len(insert_data))
                values = list(insert_data.values())

                query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
                cursor.execute(query, values)
                action = "created"

            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': f'User {action}', 'action': action})

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-test-users')
def create_test_users():
    """Создание тестовых пользователей для админ-панели"""
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        # Создаем несколько тестовых пользователей
        test_users = [
            {
                'user_id': '1001',
                'username': 'test_player_1',
                'balance': 15000,
                'level': 3,
                'level_name': 'Любитель 🟣',
                'discount': 10,
                'clicks': 4500,
                'total_earned': 18000,
                'referrals': 5
            },
            {
                'user_id': '1002',
                'username': 'test_player_2',
                'balance': 8000,
                'level': 2,
                'level_name': 'Ученик 🔵',
                'discount': 5,
                'clicks': 2800,
                'total_earned': 10000,
                'referrals': 2
            },
            {
                'user_id': '1003',
                'username': 'test_player_3',
                'balance': 25000,
                'level': 4,
                'level_name': 'Опытный 🟡',
                'discount': 15,
                'clicks': 8500,
                'total_earned': 30000,
                'referrals': 8
            }
        ]

        for user_data in test_users:
            # Проверяем существует ли пользователь
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_data['user_id'],))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO users
                    (user_id, username, balance, level, level_name, discount, clicks, total_earned, referrals)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data['username'],
                    user_data['balance'],
                    user_data['level'],
                    user_data['level_name'],
                    user_data['discount'],
                    user_data['clicks'],
                    user_data['total_earned'],
                    user_data['referrals']
                ))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Тестовые пользователи созданы',
            'count': len(test_users)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def make_odd_and_realistic(balance):
    """Делает число нечетным и добавляет случайность для правдоподобности"""
    MAX_BALANCE = 1000000

    # Ограничиваем максимальный баланс
    balance = min(balance, MAX_BALANCE)

    # Добавляем случайное число от 1 до 999 для большей правдоподобности
    balance += random.randint(1, 999)

    # Делаем нечетным
    if balance % 2 == 0:
        balance += 1

    # Ограничиваем снова после изменений
    balance = min(balance, MAX_BALANCE)

    # Для балансов близких к 1M делаем специальную обработку
    if balance > 980000:
        # Близко к 1M - используем "красивые" числа около 1M
        nice_numbers = [985421, 976853, 992147, 963259, 987653, 974321, 991237, 968745]
        balance = random.choice(nice_numbers)
    elif balance > 800000:
        # Высокие балансы - тоже "красивые" числа
        nice_numbers = [823456, 845678, 867890, 812345, 856789, 834567, 878901, 889012]
        # Находим ближайшее "красивое" число
        closest = min(nice_numbers, key=lambda x: abs(x - balance))
        balance = closest
    else:
        # Для остальных - реалистичные окончания
        last_three_digits = balance % 1000
        realistic_endings = [123, 357, 469, 571, 683, 795, 217, 439, 651, 873]
        # Заменяем последние цифры на реалистичные
        balance = balance - last_three_digits + random.choice(realistic_endings)

    return min(balance, MAX_BALANCE)

@app.route('/api/update-top-on-click', methods=['POST'])
def api_update_top_on_click():
    """Обновляет топ при клике пользователя с реалистичным приростом"""
    try:
        data = request.json
        user_balance = data.get('balance', 0)

        global current_top_players

        if current_top_players:
            MAX_BALANCE = 1000000

            # Увеличиваем балансы топ-игроков с разным реалистичным приростом
            for i, player in enumerate(current_top_players):
                current_balance = player['balance']

                # Разный прирост в зависимости от позиции и текущего баланса
                if i == 0:  # Первое место
                    # Чем выше баланс, тем медленнее рост
                    if current_balance > 900000:
                        increment = random.randint(1, 10)
                    elif current_balance > 700000:
                        increment = random.randint(5, 50)
                    else:
                        increment = random.randint(10, 100)
                elif i == 1:  # Второе место
                    if current_balance > 800000:
                        increment = random.randint(5, 30)
                    else:
                        increment = random.randint(10, 80)
                else:  # Третье место
                    increment = random.randint(15, 120)

                # Иногда (10% случаев) вообще не увеличиваем для реалистичности
                if random.random() > 0.1:
                    new_balance = min(current_balance + increment, MAX_BALANCE)
                    player['balance'] = make_odd_and_realistic(new_balance)

            # Пересортируем после изменений
            current_top_players.sort(key=lambda x: x['balance'], reverse=True)

            # Обновляем время последнего обновления
            global last_top_update
            last_top_update = datetime.now()

        return jsonify({'success': True})

    except Exception as e:
        print(f"❌ Update top on click error: {e}")
        return jsonify({'success': False})

def generate_smart_top(user_balance):
    """Генерирует умный топ с реалистичным случайным разбросом балансов"""
    # Выбираем 3 случайных ника из FAKE_USERNAMES
    selected_usernames = random.sample(FAKE_USERNAMES, 3)

    MAX_TOP_BALANCE = 1000000

    # Определяем базовый баланс для генерации
    if user_balance == 0:
        base_balance = 500000  # Стартовая точка для новых пользователей
    else:
        base_balance = user_balance

    # Генерируем три случайных баланса, которые всегда больше пользовательского
    # и имеют случайные разницы между собой
    balances = []

    # Первое место - самый высокий баланс
    first_min = max(base_balance + 1000, 600000)  # Минимум для первого места
    first_max = MAX_TOP_BALANCE
    first_balance = random.randint(first_min, min(first_max, first_min + 300000))
    balances.append(first_balance)

    # Второе место - случайная разница от первого (от 1 до 200000)
    second_diff = random.randint(1, 200000)
    second_min = max(base_balance + 500, 400000)  # Минимум для второго места
    second_balance = max(second_min, first_balance - second_diff)
    balances.append(second_balance)

    # Третье место - случайная разница от второго (от 1 до 150000)
    third_diff = random.randint(1, 150000)
    third_min = max(base_balance + 100, 200000)  # Минимум для третьего места
    third_balance = max(third_min, second_balance - third_diff)
    balances.append(third_balance)

    # Гарантируем убывающий порядок
    balances.sort(reverse=True)

    # Делаем балансы нечетными и реалистичными
    balances = [make_odd_and_realistic(balance) for balance in balances]

    # Создаем список игроков
    players = []
    for i, balance in enumerate(balances):
        players.append({
            'username': selected_usernames[i],
            'balance': balance
        })

    return players

# Обновим функцию получения топа, чтобы она учитывала обновления
@app.route('/api/smart-top-players', methods=['GET'])
def api_smart_top_players():
    """Умный топ игроков, который подстраивается под баланс пользователя"""
    try:
        user_id = request.args.get('user_id')
        user_balance = int(request.args.get('balance', 0))

        global current_top_players, last_top_update

        # Обновляем топ раз в час или если он пустой
        time_since_update = datetime.now() - last_top_update
        if not current_top_players or time_since_update.total_seconds() > 3600:
            current_top_players = generate_smart_top(user_balance)
            last_top_update = datetime.now()

        return jsonify({
            'success': True,
            'players': current_top_players,
            'next_update': (last_top_update + timedelta(hours=1)).strftime('%H:%M')
        })

    except Exception as e:
        print(f"❌ Smart Top Players Error: {e}")
        # Возвращаем случайных пользователей из FAKE_USERNAMES
        random_names = random.sample(FAKE_USERNAMES, 3)
        return jsonify({
            'success': True,
            'players': [
                {'username': random_names[0], 'balance': 985421},
                {'username': random_names[1], 'balance': 763857},
                {'username': random_names[2], 'balance': 542619}
            ],
            'next_update': '23:00'
        })

# API для получения всех пользователей (для админ-панели)
@app.route('/api/all-users')
def api_all_users():
    """API для получения всех пользователей С ПРОВЕРКОЙ ПАРОЛЯ"""
    try:
        # Проверяем пароль из параметров запроса
        password = request.args.get('password')
        print(f"🔐 Проверка пароля: {password}")  # Для отладки

        if password != 'DnK2025':
            print("❌ Неверный пароль")
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        conn = sqlite3.connect(NEW_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, username, balance, level, level_name, discount,
                   clicks, total_earned, referrals, passive_income,
                   upgrades, bonuses, energy, max_energy,
                   last_energy_update, last_passive_claim, boost,
                   created_at, updated_at
            FROM users
            ORDER BY balance DESC
        ''')

        users = cursor.fetchall()
        conn.close()

        users_list = []
        for user in users:
            user_dict = dict(user)

            # Преобразуем JSON поля в объекты
            for field in ['upgrades', 'bonuses', 'boost']:
                if user_dict.get(field) and isinstance(user_dict[field], str):
                    try:
                        user_dict[field] = json.loads(user_dict[field])
                    except:
                        user_dict[field] = {}

            users_list.append(user_dict)

        print(f"✅ Возвращаем {len(users_list)} пользователей")
        return jsonify({
            'success': True,
            'users': users_list,
            'total': len(users_list)
        })

    except Exception as e:
        print(f"❌ API All Users Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/migrate-user', methods=['POST'])
def api_migrate_user():
    """API для миграции пользователей из localStorage в базу данных"""
    try:
        data = request.json
        user_id = data.get('user_id')
        user_data = data.get('user_data')

        if not user_id or not user_data:
            return jsonify({'error': 'Missing user_id or user_data'}), 400

        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        # Проверяем существует ли пользователь
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Обновляем существующего пользователя
            cursor.execute('''
                UPDATE users SET
                    balance = ?, level = ?, level_name = ?, discount = ?,
                    clicks = ?, total_earned = ?, referrals = ?, passive_income = ?,
                    upgrades = ?, bonuses = ?, energy = ?, max_energy = ?,
                    last_energy_update = ?, last_passive_claim = ?, boost = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                user_data.get('balance', 0),
                user_data.get('level', 1),
                user_data.get('level_name', 'Новичок 🟢'),
                user_data.get('discount', 0),
                user_data.get('clicks', 0),
                user_data.get('total_earned', 0),
                user_data.get('referrals', 0),
                user_data.get('passive_income', 0),
                json.dumps(user_data.get('upgrades', {"click_power":1,"passive":0,"autoclick":0,"energy_limit":0})),
                json.dumps(user_data.get('bonuses', {"kybnk_show":false,"kybnk_shop":false})),
                user_data.get('energy', 100),
                user_data.get('max_energy', 100),
                user_data.get('last_energy_update'),
                user_data.get('last_passive_claim'),
                json.dumps(user_data.get('boost', {"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1})),
                user_id
            ))
            action = "updated"
        else:
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (
                    user_id, username, balance, level, level_name, discount,
                    clicks, total_earned, referrals, passive_income, upgrades, bonuses,
                    energy, max_energy, last_energy_update, last_passive_claim, boost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user_data.get('username', 'Web User'),
                user_data.get('balance', 0),
                user_data.get('level', 1),
                user_data.get('level_name', 'Новичок 🟢'),
                user_data.get('discount', 0),
                user_data.get('clicks', 0),
                user_data.get('total_earned', 0),
                user_data.get('referrals', 0),
                user_data.get('passive_income', 0),
                json.dumps(user_data.get('upgrades', {"click_power":1,"passive":0,"autoclick":0,"energy_limit":0})),
                json.dumps(user_data.get('bonuses', {"kybnk_show":false,"kybnk_shop":false})),
                user_data.get('energy', 100),
                user_data.get('max_energy', 100),
                user_data.get('last_energy_update'),
                user_data.get('last_passive_claim'),
                json.dumps(user_data.get('boost', {"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1}))
            ))
            action = "created"

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'User {action} successfully',
            'action': action
        })

    except Exception as e:
        print(f"Migration Error: {e}")
        return jsonify({'error': str(e)}), 500


# Веб-интерфейс для управления пользователями
@app.route('/admin/users')
def admin_users_web():
    """Современная админ-панель с реальным временем"""
    try:
        password = request.args.get('password')
        if password != 'DnK2025':
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>KYBNK - Доступ запрещен</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #0A0A0F, #15151F);
                        color: white;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                    }
                    .container {
                        text-align: center;
                        background: rgba(30, 30, 45, 0.8);
                        padding: 40px;
                        border-radius: 15px;
                        border: 1px solid rgba(255,255,255,0.1);
                    }
                    h1 { color: #FF2D75; margin-bottom: 20px; }
                    .login-form { margin: 20px 0; }
                    input {
                        padding: 12px 15px;
                        margin: 10px;
                        border: 1px solid rgba(255,255,255,0.2);
                        border-radius: 8px;
                        background: rgba(255,255,255,0.1);
                        color: white;
                        width: 200px;
                    }
                    button {
                        padding: 12px 25px;
                        background: linear-gradient(135deg, #00D4FF, #FF2D75);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔐 Доступ запрещен</h1>
                    <p>Введите пароль для доступа к админ-панели:</p>
                    <div class="login-form">
                        <input type="password" id="passwordInput" placeholder="Пароль">
                        <button onclick="checkPassword()">Войти</button>
                    </div>
                </div>
                <script>
                    function checkPassword() {
                        const password = document.getElementById('passwordInput').value;
                        if (password) {
                            window.location.href = '/admin/users?password=' + password;
                        }
                    }
                    document.getElementById('passwordInput').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') checkPassword();
                    });
                </script>
            </body>
            </html>
            """, 403

        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>KYBNK - Админ-панель</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {
                    --bg-primary: #0A0A0F;
                    --bg-secondary: #15151F;
                    --accent-blue: #00D4FF;
                    --accent-pink: #FF2D75;
                    --text-primary: #FFFFFF;
                    --text-secondary: #A0A0B0;
                }

                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: var(--bg-primary);
                    color: var(--text-primary);
                    min-height: 100vh;
                }

                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }

                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: var(--bg-secondary);
                    border-radius: 15px;
                    border: 1px solid rgba(255,255,255,0.1);
                }

                .header h1 {
                    font-size: 2em;
                    margin-bottom: 10px;
                    background: linear-gradient(135deg, var(--accent-blue), var(--accent-pink));
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }

                .search-controls {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                    gap: 15px;
                    margin-bottom: 20px;
                    padding: 20px;
                    background: rgba(0,212,255,0.1);
                    border-radius: 10px;
                }

                .search-box {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex: 1;
                    min-width: 300px;
                }

                .search-box input {
                    flex: 1;
                    padding: 12px 15px;
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 8px;
                    background: rgba(255,255,255,0.1);
                    color: white;
                    font-size: 14px;
                }

                .search-box input::placeholder {
                    color: rgba(255,255,255,0.5);
                }

                .controls {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }

                .stat-card {
                    background: rgba(30, 30, 45, 0.6);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.1);
                    text-align: center;
                    transition: all 0.3s ease;
                }

                .stat-card:hover {
                    border-color: var(--accent-blue);
                    transform: translateY(-2px);
                }

                .users-grid {
                    display: grid;
                    gap: 15px;
                    margin: 20px 0;
                }

                .user-card {
                    background: rgba(30, 30, 45, 0.6);
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid rgba(255,255,255,0.1);
                    transition: all 0.3s ease;
                }

                .user-card:hover {
                    border-color: var(--accent-blue);
                    transform: translateY(-2px);
                }

                .user-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                    gap: 10px;
                }

                .user-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin: 15px 0;
                }

                .edit-form {
                    background: rgba(0, 212, 255, 0.1);
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 15px;
                }

                .form-row {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin: 10px 0;
                    flex-wrap: wrap;
                }

                input, button, select {
                    padding: 10px 15px;
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 8px;
                    background: rgba(255,255,255,0.1);
                    color: white;
                    font-size: 14px;
                }

                button {
                    background: linear-gradient(135deg, var(--accent-blue), var(--accent-pink));
                    border: none;
                    cursor: pointer;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    white-space: nowrap;
                }

                button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(0,212,255,0.3);
                }

                button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    transform: none;
                }

                .btn-primary {
                    background: linear-gradient(135deg, var(--accent-blue), var(--accent-pink));
                }

                .btn-success {
                    background: linear-gradient(135deg, #00FF00, #00CC00);
                }

                .btn-danger {
                    background: linear-gradient(135deg, #FF2D75, #8B5CF6);
                }

                .btn-warning {
                    background: linear-gradient(135deg, #FFD700, #FFA500);
                }

                .discount-buttons {
                    display: flex;
                    gap: 5px;
                    flex-wrap: wrap;
                    margin: 10px 0;
                }

                .discount-buttons button {
                    padding: 8px 12px;
                    font-size: 12px;
                }

                .token-controls {
                    display: flex;
                    gap: 5px;
                    flex-wrap: wrap;
                    margin: 10px 0;
                }

                .token-controls button {
                    padding: 8px 12px;
                    font-size: 12px;
                }

                .loading {
                    text-align: center;
                    padding: 40px;
                    color: var(--text-secondary);
                }

                .error {
                    text-align: center;
                    padding: 20px;
                    background: rgba(255,45,117,0.1);
                    border: 1px solid var(--accent-pink);
                    border-radius: 10px;
                    margin: 20px 0;
                }

                @media (max-width: 768px) {
                    .search-controls {
                        flex-direction: column;
                        align-items: stretch;
                    }

                    .search-box {
                        min-width: auto;
                    }

                    .controls {
                        justify-content: center;
                    }

                    .user-header {
                        flex-direction: column;
                        align-items: flex-start;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👥 Админ-панель KYBNK</h1>
                    <p>Все изменения сохраняются мгновенно в базу данных</p>
                </div>

                <div class="search-controls">
                    <div class="search-box">
                        <input type="text" id="searchInput" placeholder="🔍 Поиск по имени или ID...">
                        <button onclick="searchUsers()">Поиск</button>
                    </div>
                    <div class="controls">
                        <button onclick="loadUsers()" class="btn-primary">🔄 Обновить</button>
                        <button onclick="window.location.href='/'" class="btn-primary">🎮 Игра</button>
                        <button onclick="showStats()" class="btn-primary">📊 Статистика</button>
                        <button onclick="createTestUsers()" class="btn-warning">🧪 Тест данные</button>
                    </div>
                </div>

                <div id="statsSection" style="display: none;">
                    <div class="stats-grid" id="statsGrid"></div>
                </div>

                <div id="usersList">
                    <div class="loading">Загрузка пользователей...</div>
                </div>
            </div>

            <script>
                let allUsers = [];
                const ADMIN_PASSWORD = "DnK2025";

                // Утилиты для работы с API
                async function apiCall(endpoint, options = {}) {
                    try {
                        const url = endpoint.includes('?')
                            ? `${endpoint}&password=${ADMIN_PASSWORD}`
                            : `${endpoint}?password=${ADMIN_PASSWORD}`;

                        const response = await fetch(url, {
                            headers: {
                                'Content-Type': 'application/json',
                                ...options.headers
                            },
                            ...options
                        });

                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }

                        return await response.json();
                    } catch (error) {
                        console.error('API Error:', error);
                        throw error;
                    }
                }

                // Загрузка пользователей
                async function loadUsers() {
                    try {
                        showLoading();
                        const data = await apiCall('/api/all-users');

                        if (data.success) {
                            allUsers = data.users;
                            displayUsers(allUsers);
                            updateStats(data.users);
                            console.log(`✅ Загружено ${allUsers.length} пользователей`);
                        } else {
                            throw new Error(data.error || 'Unknown error');
                        }
                    } catch (error) {
                        console.error('❌ Ошибка загрузки:', error);
                        showError('Ошибка загрузки: ' + error.message);
                    }
                }

                // Показать загрузку
                function showLoading() {
                    document.getElementById('usersList').innerHTML = '<div class="loading">Загрузка пользователей...</div>';
                }

                // Показать ошибку
                function showError(message) {
                    document.getElementById('usersList').innerHTML = `
                        <div class="error">
                            <h3>❌ Ошибка</h3>
                            <p>${message}</p>
                            <button onclick="loadUsers()" class="btn-primary">Повторить</button>
                        </div>
                    `;
                }

                // Отображение пользователей
                function displayUsers(users) {
                    const container = document.getElementById('usersList');

                    if (users.length === 0) {
                        container.innerHTML = '<div class="loading">👥 Пользователи не найдены</div>';
                        return;
                    }

                    let html = '';
                    users.forEach(user => {
                        html += `
                            <div class="user-card">
                                <div class="user-header">
                                    <h3 style="color: var(--accent-blue); margin: 0;">
                                        👤 ${user.username || 'Без имени'}
                                        <small style="color: var(--text-secondary);">(ID: ${user.user_id})</small>
                                    </h3>
                                    <span style="background: linear-gradient(135deg, var(--accent-blue), var(--accent-pink));
                                           color: white; padding: 6px 12px; border-radius: 15px; font-weight: bold;">
                                        ${user.level_name || 'Новичок 🟢'}
                                    </span>
                                </div>

                                <div class="user-stats">
                                    <div class="stat">💰 <strong style="color: var(--accent-blue);">${user.balance || 0}</strong> токенов</div>
                                    <div class="stat">🎯 Уровень <strong>${user.level || 1}</strong></div>
                                    <div class="stat">🎫 Скидка <strong style="color: #FFD700;">${user.discount || 0}%</strong></div>
                                    <div class="stat">🖱️ <strong>${user.clicks || 0}</strong> кликов</div>
                                    <div class="stat">📈 Всего <strong>${user.total_earned || 0}</strong></div>
                                    <div class="stat">👥 Рефералов <strong>${user.referrals || 0}</strong></div>
                                </div>

                                <div class="edit-form">
                                    <strong style="color: var(--accent-blue);">✏️ Быстрое редактирование:</strong>

                                    <div class="form-row">
                                        <label>💰 Баланс:</label>
                                        <input type="number" id="balance_${user.user_id}" value="${user.balance || 0}" style="width: 120px;">
                                        <button onclick="updateUser('${user.user_id}')" class="btn-primary">💾 Сохранить</button>
                                    </div>

                                    <div class="form-row">
                                        <label>🎫 Скидка (%):</label>
                                        <input type="number" id="discount_${user.user_id}" value="${user.discount || 0}" min="0" max="100" style="width: 80px;">
                                        <button onclick="updateUser('${user.user_id}')" class="btn-primary">💾 Сохранить</button>
                                    </div>

                                    <div class="discount-buttons">
                                        <button onclick="setDiscount('${user.user_id}', 5)" class="btn-primary">🎯 5%</button>
                                        <button onclick="setDiscount('${user.user_id}', 10)" class="btn-primary">🎯 10%</button>
                                        <button onclick="setDiscount('${user.user_id}', 15)" class="btn-primary">🎯 15%</button>
                                        <button onclick="setDiscount('${user.user_id}', 20)" class="btn-primary">🎯 20%</button>
                                    </div>

                                    <div class="token-controls">
                                        <button onclick="addTokens('${user.user_id}', 1000)" class="btn-success">➕ 1000</button>
                                        <button onclick="addTokens('${user.user_id}', 5000)" class="btn-success">➕ 5000</button>
                                        <button onclick="addTokens('${user.user_id}', 10000)" class="btn-success">➕ 10000</button>
                                        <button onclick="addTokens('${user.user_id}', -1000)" class="btn-danger">➖ 1000</button>
                                        <button onclick="addTokens('${user.user_id}', -5000)" class="btn-danger">➖ 5000</button>
                                    </div>
                                </div>

                                <div style="margin-top: 10px; font-size: 0.9em; color: var(--text-secondary);">
                                    📅 Зарегистрирован: ${user.created_at || 'N/A'}
                                    ${user.updated_at && user.updated_at !== user.created_at ? ` | 📝 Обновлен: ${user.updated_at}` : ''}
                                </div>
                            </div>
                        `;
                    });

                    container.innerHTML = html;
                }

                // Обновление пользователя
                async function updateUser(userId) {
                    try {
                        const balance = document.getElementById('balance_' + userId).value;
                        const discount = document.getElementById('discount_' + userId).value;

                        await apiCall('/api/user/' + userId, {
                            method: 'POST',
                            body: JSON.stringify({
                                balance: parseInt(balance) || 0,
                                discount: parseInt(discount) || 0
                            })
                        });

                        console.log('✅ Пользователь обновлен:', userId);
                        // Показываем уведомление об успехе
                        showTempMessage('✅ Изменения сохранены', 'success');

                    } catch (error) {
                        console.error('❌ Ошибка обновления:', error);
                        showTempMessage('❌ Ошибка сохранения: ' + error.message, 'error');
                    }
                }

                // Вспомогательные функции
                function addTokens(userId, amount) {
                    const balanceInput = document.getElementById('balance_' + userId);
                    const currentBalance = parseInt(balanceInput.value) || 0;
                    balanceInput.value = currentBalance + amount;
                    updateUser(userId);
                }

                function setDiscount(userId, discount) {
                    document.getElementById('discount_' + userId).value = discount;
                    updateUser(userId);
                }

                function searchUsers() {
                    const term = document.getElementById('searchInput').value.toLowerCase();
                    const filtered = allUsers.filter(user =>
                        (user.username && user.username.toLowerCase().includes(term)) ||
                        (user.user_id && user.user_id.toLowerCase().includes(term))
                    );
                    displayUsers(filtered);
                }

                function showStats() {
                    const statsSection = document.getElementById('statsSection');
                    statsSection.style.display = statsSection.style.display === 'none' ? 'block' : 'none';
                }

                function updateStats(users) {
                    const totalBalance = users.reduce((sum, user) => sum + (user.balance || 0), 0);
                    const totalUsers = users.length;
                    const totalClicks = users.reduce((sum, user) => sum + (user.clicks || 0), 0);
                    const avgLevel = users.length > 0 ? users.reduce((sum, user) => sum + (user.level || 1), 0) / users.length : 0;
                    const totalReferrals = users.reduce((sum, user) => sum + (user.referrals || 0), 0);

                    document.getElementById('statsGrid').innerHTML = `
                        <div class="stat-card">
                            <div>👥 Всего пользователей</div>
                            <div style="font-size: 1.5em; font-weight: bold; color: var(--accent-blue);">${totalUsers}</div>
                        </div>
                        <div class="stat-card">
                            <div>💰 Общий баланс</div>
                            <div style="font-size: 1.5em; font-weight: bold; color: var(--accent-blue);">${totalBalance.toLocaleString()}</div>
                        </div>
                        <div class="stat-card">
                            <div>🖱️ Всего кликов</div>
                            <div style="font-size: 1.5em; font-weight: bold; color: var(--accent-blue);">${totalClicks.toLocaleString()}</div>
                        </div>
                        <div class="stat-card">
                            <div>📊 Средний уровень</div>
                            <div style="font-size: 1.5em; font-weight: bold; color: var(--accent-blue);">${avgLevel.toFixed(1)}</div>
                        </div>
                        <div class="stat-card">
                            <div>👥 Всего рефералов</div>
                            <div style="font-size: 1.5em; font-weight: bold; color: var(--accent-blue);">${totalReferrals}</div>
                        </div>
                    `;
                }

                // Временное сообщение
                function showTempMessage(message, type = 'info') {
                    const messageDiv = document.createElement('div');
                    messageDiv.style.cssText = `
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        padding: 15px 20px;
                        border-radius: 8px;
                        color: white;
                        font-weight: bold;
                        z-index: 10000;
                        background: ${type === 'success' ? 'linear-gradient(135deg, #00FF00, #00CC00)' : 'linear-gradient(135deg, #FF2D75, #8B5CF6)'};
                        border: 1px solid rgba(255,255,255,0.2);
                        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                    `;
                    messageDiv.textContent = message;

                    document.body.appendChild(messageDiv);

                    setTimeout(() => {
                        if (messageDiv.parentNode) {
                            messageDiv.parentNode.removeChild(messageDiv);
                        }
                    }, 3000);
                }

                // Создание тестовых пользователей
                async function createTestUsers() {
                    if (!confirm('Создать тестовых пользователей? Это для отладки.')) return;

                    try {
                        const response = await fetch('/api/create-test-users?password=' + ADMIN_PASSWORD);
                        const data = await response.json();

                        if (data.success) {
                            showTempMessage(`✅ Создано ${data.count} тестовых пользователей`, 'success');
                            loadUsers(); // Перезагружаем список
                        } else {
                            showTempMessage('❌ Ошибка: ' + data.error, 'error');
                        }
                    } catch (error) {
                        showTempMessage('❌ Ошибка сети: ' + error.message, 'error');
                    }
                }

                // Авто-обновление каждые 30 секунд
                setInterval(loadUsers, 30000);

                // Загружаем данные при старте
                document.addEventListener('DOMContentLoaded', function() {
                    loadUsers();
                });

                // Поиск при вводе
                document.getElementById('searchInput').addEventListener('input', searchUsers);

                // Поиск при нажатии Enter
                document.getElementById('searchInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchUsers();
                    }
                });
            </script>
        </body>
        </html>
        '''

    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; margin: 20px; background: #0A0A0F; color: white;">
            <h1 style="color: #FF2D75;">❌ Ошибка сервера</h1>
            <p>Произошла ошибка при загрузке админ-панели:</p>
            <pre style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">{str(e)}</pre>
            <button onclick="window.location.href='/'" style="padding: 10px 20px; background: #00D4FF; color: white; border: none; border-radius: 8px; cursor: pointer;">← Вернуться в игру</button>
        </body>
        </html>
        """, 500

@app.route('/api/admin/reset-all', methods=['POST'])
def admin_reset_all():
    """API для сброса всех пользователей (только для админа)"""
    try:
        data = request.json
        password = data.get('password')

        if password != 'DnK2025':
            return jsonify({'error': 'Access denied'}), 403

        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        # Сбрасываем всех пользователей к начальным значениям
        cursor.execute('''
            UPDATE users SET
                balance = 0,
                level = 1,
                level_name = 'Новичок 🟢',
                discount = 0,
                clicks = 0,
                total_earned = 0,
                referrals = 0,
                passive_income = 0,
                upgrades = '{"click_power":1,"passive":0,"autoclick":0,"energy_limit":0}',
                bonuses = '{"kybnk_show":false,"kybnk_shop":false}',
                energy = 100,
                max_energy = 100,
                last_energy_update = ?,
                last_passive_claim = ?,
                boost = '{"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1}',
                updated_at = CURRENT_TIMESTAMP
        ''', (int(datetime.datetime.now().timestamp() * 1000),
              int(datetime.datetime.now().timestamp() * 1000)))

        conn.commit()

        # Получаем количество обновленных пользователей
        cursor.execute('SELECT changes()')
        updated_count = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'message': f'Сброшено {updated_count} пользователей',
            'reset_count': updated_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/force-update-top', methods=['POST'])
def api_force_update_top():
    """Принудительное обновление топа (только для админа)"""
    try:
        password = request.json.get('password')

        if password != 'DnK2025':
            return jsonify({'error': 'Access denied'}), 403

        global current_top_players, last_top_update
        current_top_players = []  # Принудительно сбрасываем топ
        last_top_update = datetime.now() - timedelta(hours=2)  # Заставляем обновиться

        return jsonify({
            'success': True,
            'message': 'Топ игроков будет обновлен при следующем запросе'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API для получения топа игроков
@app.route('/api/top-players', methods=['GET'])
def api_top_players():
    """API для получения топ-3 игроков по балансу"""
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получаем топ-3 игроков по балансу с реальными именами
        cursor.execute('''
            SELECT user_id, username, balance, level, level_name
            FROM users
            WHERE username IS NOT NULL AND username != '' AND balance > 0
            ORDER BY balance DESC
            LIMIT 3
        ''')

        top_players = cursor.fetchall()
        conn.close()

        # Форматируем данные для ответа
        players_list = []
        for player in top_players:
            username = player['username']
            # Если username не начинается с @, добавляем его
            if username and not username.startswith('@'):
                username = '@' + username

            players_list.append({
                'username': username or f"user_{player['user_id']}",
                'balance': player['balance'],
                'level': player['level'],
                'level_name': player['level_name']
            })

        # Если игроков меньше 3, дополняем реальными пользователями с нулевым балансом
        if len(players_list) < 3:
            conn = sqlite3.connect(NEW_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, username, balance, level, level_name
                FROM users
                WHERE (username IS NOT NULL AND username != '')
                ORDER BY created_at DESC
                LIMIT ?
            ''', (3 - len(players_list),))

            additional_players = cursor.fetchall()
            conn.close()

            for player in additional_players:
                if len(players_list) >= 3:
                    break

                username = player['username']
                if username and not username.startswith('@'):
                    username = '@' + username

                players_list.append({
                    'username': username or f"user_{player['user_id']}",
                    'balance': player['balance'] or 0,
                    'level': player['level'],
                    'level_name': player['level_name']
                })

        # Если все еще меньше 3, дополняем заглушками
        while len(players_list) < 3:
            players_list.append({
                'username': f'@player_{len(players_list) + 1}',
                'balance': 0,
                'level': 1,
                'level_name': 'Новичок 🟢'
            })

        print(f"✅ Top players API returned: {players_list}")  # Для отладки

        return jsonify({
            'success': True,
            'players': players_list
        })

    except Exception as e:
        print(f"❌ API Top Players Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'players': [
                {'username': '@top_player', 'balance': 1250000},
                {'username': '@second_place', 'balance': 987500},
                {'username': '@third_user', 'balance': 756300}
            ]
        })

@app.route('/debug')
def debug_info():
    import datetime
    info = {
        "current_time": str(datetime.datetime.now()),
        "file_path": os.path.abspath(__file__),
        "file_mod_time": str(datetime.datetime.fromtimestamp(os.path.getmtime(__file__))),
        "files_in_directory": os.listdir('.'),
        "python_version": os.sys.version,
        "flask_version": "unknown",
        "database_path": NEW_DB_PATH,
        "database_exists": os.path.exists(NEW_DB_PATH)
    }

    try:
        import flask
        info["flask_version"] = flask.__version__
    except:
        pass

    return jsonify(info)

@app.route('/api/debug-users')
def debug_users():
    """Маршрут для отладки - показывает всех пользователей"""
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT user_id, username, balance, level, level_name
            FROM users
            ORDER BY balance DESC
        ''')

        all_users = cursor.fetchall()
        conn.close()

        users_list = []
        for user in all_users:
            users_list.append(dict(user))

        return jsonify({
            'total_users': len(users_list),
            'users': users_list
        })

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/db-status')
def api_db_status():
    """Проверка статуса базы данных"""
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        # Проверяем количество пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]

        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        # Получаем несколько пользователей для примера
        cursor.execute('SELECT user_id, username, balance FROM users LIMIT 5')
        sample_users = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'database_path': NEW_DB_PATH,
            'user_count': user_count,
            'columns': columns,
            'sample_users': sample_users,
            'database_exists': os.path.exists(NEW_DB_PATH)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test/click')
def test_click():
    return "Функция клика тест - НОВАЯ ВЕРСИЯ"

@app.route('/test/shop')
def test_shop():
    return "Магазин тест - НОВАЯ ВЕРСИЯ"

@app.route('/test/admin')
def test_admin():
    return "Админка тест - НОВАЯ ВЕРСИЯ"

@app.route('/test-direct')
def test_direct():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>ПРЯМОЙ ДОСТУП - НОВАЯ ВЕРСИЯ</title></head>
    <body>
        <h1 style="color: green;">✅ ЭТО НОВАЯ ВЕРСИЯ APP.PY!</h1>
        <p>Если вы видите это, значит загружен правильный app.py из папки webapp</p>
        <p>Время: <span id="time"></span></p>
        <script>
            document.getElementById('time').textContent = new Date().toLocaleString();
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)