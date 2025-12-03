#!/usr/bin/env python3
import os
import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
import datetime
import json
from contextlib import asynccontextmanager

# Настройки
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU")
ADMIN_IDS = [7533352996]

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Путь к базе данных
if 'RAILWAY_ENVIRONMENT' in os.environ:
    # На Railway используем временную директорию
    DB_PATH = '/tmp/kybnk_game.db'
else:
    DB_PATH = 'kybnk_game.db'

def ensure_database():
    """Создаем базу данных при запуске"""
    try:
        logger.info(f"🔧 Создание БД по пути: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Таблица пользователей
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Индексы для скорости
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных готова")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        return False

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Проверяем аргументы для реферальной системы
    referrer_id = None
    if context.args:
        for arg in context.args:
            if arg.startswith('ref_'):
                referrer_id = arg[4:]
                break
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (user_id, username, balance, level, level_name, discount, clicks, total_earned, referrals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user.username or user.first_name or "Пользователь",
                0,  # balance
                1,  # level
                'Новичок 🟢',  # level_name
                0,  # discount
                0,  # clicks
                0,  # total_earned
                0   # referrals
            ))
            
            # Реферальная система
            if referrer_id and referrer_id != user_id:
                try:
                    # Даем бонусы
                    cursor.execute('UPDATE users SET balance = balance + 1000 WHERE user_id = ?', (user_id,))
                    cursor.execute('UPDATE users SET balance = balance + 2000, referrals = referrals + 1 WHERE user_id = ?', (referrer_id,))
                    
                    # Отправляем уведомление рефереру
                    try:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 По вашей реферальной ссылке присоединился: @{user.username or user.first_name}\n\n"
                                 f"💎 Вы получили: 2000 токенов\n"
                                 f"🎁 Друг получил: 1000 токенов",
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление: {e}")
                        
                except Exception as e:
                    logger.error(f"Ошибка реферальной системы: {e}")
            
            logger.info(f"✅ Создан пользователь: {user_id}")
        else:
            # Обновляем username если изменился
            cursor.execute('UPDATE users SET username = ? WHERE user_id = ?', 
                         (user.username or user.first_name, user_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения пользователя: {e}")
    
    # Формируем ответ
    user_name = user.first_name or "Дорогой пользователь"
    referral_link = f"https://t.me/kybnk_show_bot?start=ref_{user_id}"
    
    welcome_text = (
        f"<b>{user_name}</b>, <b>добро пожаловать в KYBNK SHOW!</b>\n\n"
        "🎮 Ваш прогресс теперь сохраняется на сервере!\n"
        "💎 Получайте токены и обменивайте их на товары\n\n"
        
        "👥 <b>Реферальная система:</b>\n"
        "• Пригласи друга и получи <b>2000 токенов</b>\n"
        "• Друг получит <b>1000 токенов</b> за регистрацию\n\n"
        
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        
        "Для доступа к игре перейдите по ссылке:\n"
        "https://kybnkshow.pythonanywhere.com/\n\n"
        "Там вас ждет увлекательная игра-кликер с токенами и магазином!"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

# Команда /admin
async def admin_command(update: Update, context: CallbackContext) -> None:
    """Команда админ-панели"""
    user_id = str(update.effective_user.id)
    
    if user_id != "7533352996":
        await update.message.reply_text("❌ У вас нет прав доступа к админ-панели.")
        return
    
    keyboard = [
        [KeyboardButton("📊 Статистика")],
        [KeyboardButton("🎮 Веб-версия")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "⚙️ Админ-панель KYBNK кликер\n\n"
        "Доступ к веб-интерфейсу:\n"
        "https://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений"""
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    if user_id != "7533352996":
        return
    
    if text == "📊 Статистика":
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(balance) FROM users")
            total_balance = cursor.fetchone()[0] or 0
            
            conn.close()
            
            message = (
                "📊 Статистика бота\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"💰 Всего токенов в системе: {total_balance}\n"
                f"📅 Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}"
            )
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await update.message.reply_text("❌ Ошибка при получении статистики")
    
    elif text == "🎮 Веб-версия":
        await update.message.reply_text(
            "🎮 Открыть веб-версию игры:\n"
            "https://kybnkshow.pythonanywhere.com/"
        )

# Основная функция
async def main() -> None:
    """Запуск бота"""
    logger.info("🔄 Инициализация базы данных...")
    ensure_database()
    
    # Создаем Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("🤖 Бот запускается...")
    
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        # На Railway используем вебхуки
        webhook_url = os.environ.get('RAILWAY_STATIC_URL')
        if webhook_url:
            webhook_url = f"{webhook_url}/webhook"
            await application.bot.set_webhook(webhook_url)
            logger.info(f"🌐 Вебхук установлен: {webhook_url}")
            
            # Запускаем веб-сервер для Railway
            from fastapi import FastAPI
            import uvicorn
            from telegram import Update
            from telegram.ext import Application
            
            app = FastAPI()
            
            @app.post("/webhook")
            async def webhook(update: dict):
                """Обработчик вебхука"""
                telegram_update = Update.de_json(update, application.bot)
                await application.process_update(telegram_update)
                return {"status": "ok"}
            
            @app.get("/")
            async def health():
                """Проверка здоровья"""
                return {"status": "Bot is running"}
            
            port = int(os.environ.get("PORT", 8000))
            config = uvicorn.Config(app, host="0.0.0.0", port=port)
            server = uvicorn.Server(config)
            await server.serve()
        else:
            logger.error("❌ RAILWAY_STATIC_URL не установлен!")
    else:
        # Локально используем polling
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Бесконечный цикл
        logger.info("✅ Бот успешно запущен")
        await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
