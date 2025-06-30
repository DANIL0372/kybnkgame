import redis
import json
import os


class Database:
    def __init__(self):
        redis_url = os.getenv('REDIS_URL')
        print(f"Подключение к Redis: {redis_url}")

        try:
            self.db = redis.from_url(redis_url, decode_responses=True)
            self.db.ping()
            print("Успешное подключение к Redis!")
        except Exception as e:
            print(f"Ошибка подключения к Redis: {str(e)}")
            raise

    def user_exists(self, user_id):
        return self.db.exists(f'user:{user_id}')

    def get_or_create_user(self, user_id):
        if self.user_exists(user_id):
            return self.get_user(user_id)

        # Создаем нового пользователя
        user_data = {
            'coins': 100,  # Стартовые монеты
            'click_power': 1,
            'auto_clickers': 0,
            'last_click': 0
        }
        self.db.set(f'user:{user_id}', json.dumps(user_data))
        return user_data

    def get_user(self, user_id):
        user_data = json.loads(self.db.get(f'user:{user_id}'))
        return user_data

    def update_user(self, user_id, field, value):
        user_data = self.get_user(user_id)
        user_data[field] = value
        self.db.set(f'user:{user_id}', json.dumps(user_data))
        return user_data