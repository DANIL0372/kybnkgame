import redis
import os
import logging


class Database:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Получаем URL из переменных окружения
        redis_url = os.getenv('REDIS_URL')

        # Если URL не найден, используем локальный Redis
        if not redis_url:
            redis_url = "redis://localhost:6379"
            self.logger.warning(f"Using default Redis URL: {redis_url}")
        else:
            self.logger.info(f"Using Redis URL: {redis_url}")

        try:
            self.db = redis.from_url(redis_url, decode_responses=True)
            self.db.ping()  # Проверка подключения
            self.logger.info("Redis connection successful!")
        except Exception as e:
            self.logger.error(f"Redis connection failed: {str(e)}")
            raise