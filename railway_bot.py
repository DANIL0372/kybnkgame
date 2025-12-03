#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        user_id = str(user.id)
        
        welcome_text = f"""🎮 <b>Добро пожаловать в KYBNK GAME, {user.first_name}!</b>

🚀 Игра доступна по ссылке:
https://kybnkgame-production.up.railway.app/

🔥 Кликай, зарабатывай токены
🛍️ Обменивай их на товары
👥 Приглашай друзей и получай бонусы

🔗 <b>Ваша реферальная ссылка:</b>
https://t.me/kybnk_show_bot?start=ref_{user_id}

Пригласи друга и получи 2000 токенов!"""
        
        await update.message.reply_text(welcome_text, parse_mode='HTML')
        logger.info(f"✅ Ответил на /start пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в команде start: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """📚 <b>Команды бота:</b>
/start - Начать игру
/help - Помощь по командам

🌐 <b>Веб-версия игры:</b>
https://kybnkgame-production.up.railway.app/

🛍️ <b>Наш магазин:</b>
@kybnk_shop

📺 <b>Наш канал:</b>
@kybnk_show"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса бота"""
    await update.message.reply_text("✅ Бот работает исправно!")

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("🚀 Запуск бота KYBNK...")
        
        # Создаем Application (новый стиль для v20.x)
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status))
        
        # Запускаем бота в режиме polling
        logger.info("🤖 Бот запущен и готов к работе...")
        application.run_polling(
            poll_interval=3.0,
            timeout=20,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
