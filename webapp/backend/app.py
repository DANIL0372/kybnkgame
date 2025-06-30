import os
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from database import Database
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
db = Database()

# Путь к фронтенду относительно этого файла
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
logger.info(f"FRONTEND_DIR: {FRONTEND_DIR}")


# Главная страница - index.html
@app.route('/')
def serve_index():
    logger.info("Запрос главной страницы")
    try:
        return send_from_directory(FRONTEND_DIR, 'index.html')
    except Exception as e:
        logger.error(f"Ошибка при загрузке index.html: {str(e)}")
        return "Файл index.html не найден", 404


# Статические файлы (CSS, JS)
@app.route('/<path:filename>')
def serve_static(filename):
    logger.info(f"Запрос статического файла: {filename}")
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except Exception as e:
        logger.error(f"Файл не найден: {filename} - {str(e)}")
        return "Файл не найден", 404


# API Endpoints
@app.route('/api/user', methods=['POST'])
def create_user():
    """Создание или получение данных пользователя"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    user_data = db.get_or_create_user(user_id)
    return jsonify(user_data)


@app.route('/api/click', methods=['POST'])
def handle_click():
    """Обработка клика по монете"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    user_data = db.get_user(user_id)
    coins_to_add = user_data['click_power']

    # Обновляем баланс
    new_balance = user_data['coins'] + coins_to_add
    db.update_user(user_id, 'coins', new_balance)
    db.update_user(user_id, 'last_click', int(time.time()))

    return jsonify({
        'success': True,
        'coins_added': coins_to_add,
        'new_balance': new_balance
    })


@app.route('/api/upgrade', methods=['POST'])
def handle_upgrade():
    """Покупка улучшения"""
    user_id = request.json.get('user_id')
    upgrade_type = request.json.get('type')

    if not user_id or not upgrade_type:
        return jsonify({'error': 'Invalid request'}), 400

    user_data = db.get_user(user_id)
    cost = 0
    success = False

    if upgrade_type == 'click_power':
        cost = user_data['click_power'] * 10
        if user_data['coins'] >= cost:
            db.update_user(user_id, 'coins', user_data['coins'] - cost)
            db.update_user(user_id, 'click_power', user_data['click_power'] + 1)
            success = True

    elif upgrade_type == 'auto_clicker':
        cost = 100 * (user_data['auto_clickers'] + 1)
        if user_data['coins'] >= cost:
            db.update_user(user_id, 'coins', user_data['coins'] - cost)
            db.update_user(user_id, 'auto_clickers', user_data['auto_clickers'] + 1)
            success = True

    return jsonify({
        'success': success,
        'new_balance': user_data['coins'] - cost if success else user_data['coins'],
        'cost': cost
    })


if __name__ == '__main__':
    # Проверяем существование index.html
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    logger.info(f"Проверка index.html: {'существует' if os.path.exists(index_path) else 'не существует'}")

    app.run(debug=True, host='0.0.0.0', port=5000)