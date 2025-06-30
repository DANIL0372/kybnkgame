import redis

# Прямое подключение без URL
r = redis.Redis(
    host='redis-12353.c8.us-east-1-2.ec2.redns.redis-cloud.com',
    port=12353,
    username='default',
    password='o2BP4MGFgvKTm4BNmbz3n8A2trnWuWGR',
    decode_responses=True
)

try:
    # Проверка подключения
    print("Проверка подключения...")
    if r.ping():
        print("Успех! Redis доступен")

    # Тест записи/чтения
    print("\nТест записи...")
    r.set('test_key', 'Hello Redis!')
    value = r.get('test_key')
    print(f"Получено значение: {value}")

except Exception as e:
    print(f"Ошибка подключения: {e}")
    print("Проверьте:")
    print("1. Правильность host, port, username и password")
    print("2. Ваш IP добавлен в разрешенные в Redis Cloud")
    print("3. База данных активна")