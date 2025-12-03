#!/usr/bin/env python3
import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
from datetime import datetime

# Настройки
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU')
ADMIN_ID = 7533352996

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'kybnk_game.db')

def init_database():
    """Инициализация базы данных"""
    try:
        logger.info(f"🔄 Инициализация базы данных...")
        logger.info(f"🔧 Создание БД по пути: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
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
                theme TEXT DEFAULT 'dark',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных готова")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False

async def start_command(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        user_id = str(user.id)
        
        logger.info(f"👤 Команда /start от пользователя {user_id} ({user.username})")
        
        # Инициализация базы данных при необходимости
        init_database()
        
        # Подключаемся к БД
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        # Обработка реферальной ссылки
        referrer_id = None
        if context.args:
            for arg in context.args:
                if arg.startswith('ref_'):
                    referrer_id = arg[4:]
                    break
        
        if not existing_user:
            # Создаем нового пользователя
            cursor.execute('''
                INSERT INTO users (user_id, username, balance, level, level_name, referrals)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user.username or user.first_name or "Пользователь",
                0, 1, 'Новичок 🟢', 0
            ))
            
            # Реферальная система
            if referrer_id and referrer_id != user_id:
                try:
                    # Начисляем бонусы рефереру
                    cursor.execute('UPDATE users SET balance = balance + 2000, referrals = referrals + 1 WHERE user_id = ?', 
                                 (referrer_id,))
                    
                    # Начисляем бонусы новому пользователю
                    cursor.execute('UPDATE users SET balance = balance + 1000 WHERE user_id = ?', 
                                 (user_id,))
                    
                    # Отправляем уведомление рефереру
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 По вашей реферальной ссылке присоединился @{user.username or user.first_name}!\n"
                             f"💎 Вы получили 2000 токенов\n"
                             f"🎁 Друг получил 1000 токенов",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Ошибка реферальной системы: {e}")
            
            conn.commit()
            logger.info(f"✅ Создан новый пользователь: {user_id}")
        
        conn.close()
        
        # Формируем ответ
        if referrer_id:
            welcome_text = f"""🎉 <b>Добро пожаловать, {user.first_name}!</b>

Вы присоединились по реферальной ссылке!
✅ Вы получили: <b>1000 токенов</b>
🎁 Ваш друг получил: <b>2000 токенов</b>

Для игры перейдите на сайт:
https://kybnkgame-production.up.railway.app/
"""
        else:
            welcome_text = f"""🎮 <b>Добро пожаловать в KYBNK GAME, {user.first_name}!</b>

🔥 Получайте токены кликами
🛍️ Обменивайте их на товары
👥 Приглашайте друзей и получайте бонусы

Для начала игры перейдите по ссылке:
https://kybnkgame-production.up.railway.app/

🔗 <b>Ваша реферальная ссылка:</b>
https://t.me/kybnk_show_bot?start=ref_{user_id}

Приглашайте друзей и получайте 2000 токенов за каждого!
"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде /start: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

async def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    help_text = """📚 <b>Доступные команды:</b>

/start - Начать игру
/help - Помощь по командам
/balance - Проверить баланс
/status - Статус бота

🌐 <b>Веб-версия игры:</b>
https://kybnkgame-production.up.railway.app/

🛍️ <b>Наш магазин:</b>
@kybnk_shop

📺 <b>Наш канал:</b>
@kybnk_show

Приятной игры! 🎮"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def balance_command(update: Update, context: CallbackContext):
    """Проверка баланса"""
    try:
        user_id = str(update.effective_user.id)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            balance = result[0]
            await update.message.reply_text(f"💰 Ваш баланс: <b>{balance}</b> токенов", parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Пользователь не найден. Используйте /start")
        
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка проверки баланса: {e}")
        await update.message.reply_text("⚠️ Ошибка при проверке баланса")

async def status_command(update: Update, context: CallbackContext):
    """Статус бота"""
    status_text = f"""🤖 <b>Статус KYBNK бота</b>

✅ Бот работает исправно
🕐 Время сервера: {datetime.now().strftime('%H:%M:%S')}
📅 Дата: {datetime.now().strftime('%d.%m.%Y')}

🌐 Веб-версия доступна по ссылке:
https://kybnkgame-production.up.railway.app/

📊 <b>Для админов:</b>
/admin - Админ-панель"""
    
    await update.message.reply_text(status_text, parse_mode='HTML')

async def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Произошла ошибка. Пожалуйста, попробуйте позже."
        )

def main():
    """Основная функция запуска бота"""
    try:
        # Инициализация базы данных
        if not init_database():
            logger.error("❌ Не удалось инициализировать базу данных")
            return
        
        # Создаем Application
        logger.info("🚀 Создание Application...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("status", status_command))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запускаем бота в режиме polling
        logger.info("🔄 Запуск бота в режиме polling...")
        application.run_polling(
            poll_interval=3.0,
            timeout=20,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    logger.info("🎮 Запуск KYBNK Telegram бота...")
    main()
