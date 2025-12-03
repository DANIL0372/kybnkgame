#!/usr/bin/env python3
import os
import logging
from telegram.ext import Updater, CommandHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU')

def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""🎮 <b>Добро пожаловать в KYBNK GAME, {user.first_name}!</b>

🚀 Игра доступна по ссылке:
https://kybnkgame-production.up.railway.app/

🔥 Кликай, зарабатывай токены
🛍️ Обменивай их на товары
👥 Приглашай друзей и получай бонусы

🔗 <b>Ваша реферальная ссылка:</b>
https://t.me/kybnk_show_bot?start=ref_{user.id}

Пригласи друга и получи 2000 токенов!"""
    
    update.message.reply_text(welcome_text, parse_mode='HTML')

def help_command(update, context):
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
    
    update.message.reply_text(help_text, parse_mode='HTML')

def main():
    """Основная функция"""
    logger.info("🚀 Запуск бота KYBNK...")
    
    # Создаем Updater (старый стиль, но надежный)
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Добавляем обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Запускаем бота
    logger.info("🤖 Бот запущен и готов к работе")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
