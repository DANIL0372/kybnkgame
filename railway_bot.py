#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3
import datetime
import json

# Настройки
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU')
ADMIN_IDS = [7533352996]
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('RAILWAY_STATIC_URL', '') + '/webhook'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_DB_PATH = os.path.join(BASE_DIR, 'kybnk_game.db')

def create_new_database():
    """Создает новую базу данных"""
    try:
        logger.info(f"Создание базы данных: {NEW_DB_PATH}")
        conn = sqlite3.connect(NEW_DB_PATH)
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("✅ База данных создана")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user_id = str(update.effective_user.id)
    user = update.effective_user
    
    # Реферальная система
    referrer_id = None
    if context.args:
        for arg in context.args:
            if arg.startswith('ref_'):
                referrer_id = arg[4:]
                break
    
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            cursor.execute('''
                INSERT INTO users
                (user_id, username, balance, level, level_name, discount,
                 clicks, total_earned, referrals, passive_income, upgrades, bonuses)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user.username or user.first_name or "Пользователь",
                0, 1, 'Новичок 🟢', 0, 0, 0, 0, 0.0,
                '{"click_power":1,"passive":0,"autoclick":0,"energy_limit":0}',
                '{"kybnk_show":false,"kybnk_shop":false}'
            ))
            
            # Реферальные бонусы
            if referrer_id and referrer_id != user_id:
                cursor.execute('UPDATE users SET balance = balance + 1000 WHERE user_id = ?', (user_id,))
                cursor.execute('UPDATE users SET balance = balance + 2000, referrals = referrals + 1 WHERE user_id = ?',
                             (referrer_id,))
                
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 По вашей реферальной ссылке присоединился: @{user.username or user.first_name or 'новый пользователь'}\n\n"
                             f"💎 Вы получили: 2000 токенов\n"
                             f"🎁 Друг получил: 1000 токенов",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление: {e}")
            
            conn.commit()
            logger.info(f"✅ Создан пользователь: {user_id}")
        else:
            logger.info(f"ℹ️ Пользователь уже существует: {user_id}")
        
        conn.close()
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    # Приветственное сообщение
    referral_link = f"https://t.me/kybnk_show_bot?start=ref_{user_id}"
    welcome_text = (
        f"<b>{user.first_name or 'Дорогой пользователь'}</b>, <b>добро пожаловать в KYBNK SHOW!</b>\n\n"
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

def main() -> None:
    """Основная функция"""
    # Создаем базу данных
    create_new_database()
    
    # Создаем Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Настраиваем вебхук или polling
    if WEBHOOK_URL and 'railway' in WEBHOOK_URL:
        logger.info(f"🚀 Настраиваем вебхук: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )
    else:
        logger.info("🔄 Запускаем в режиме polling...")
        application.run_polling()

if __name__ == '__main__':
    main()
