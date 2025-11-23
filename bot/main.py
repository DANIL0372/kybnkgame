import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
import datetime
import json

# Настройки
BOT_TOKEN = "7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU"
ADMIN_ID = "7533352996"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user = update.effective_user

    # Проверяем является ли пользователь администратором
    is_admin = user_id == ADMIN_ID
    
    if is_admin:
        # Показываем админ-панель администратору
        show_admin_panel(update, context)
    else:
        # Обычным пользователям показываем ссылку на игру
        user_name = user.first_name or "Дорогой пользователь"
        
        welcome_text = (
            f"<b>{user_name}</b>, <b>добро пожаловать в KYBNK SHOW!</b>\n\n"
            "🎮 <b>Доступ к игре:</b>\n"
            "https://kybnkshow.pythonanywhere.com/\n\n"
            "💰 <b>Зарабатывай токены и обменивай их на товары!</b>\n\n"
            "👥 <b>Реферальная система:</b>\n"
            f"https://t.me/kybnk_show_bot?start=ref_{user_id}"
        )

        update.message.reply_text(welcome_text, parse_mode='HTML')

# Показать админ-панель
def show_admin_panel(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton("📊 Статистика"), KeyboardButton("👥 Пользователи")],
        [KeyboardButton("🎁 Выдать токены"), KeyboardButton("⚙️ Настройки")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    admin_text = (
        "⚙️ <b>Админ-панель KYBNK</b>\n\n"
        "🌐 <b>Веб-интерфейс:</b>\n"
        "https://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025\n\n"
        "🎮 <b>Игра:</b>\n"
        "https://kybnkshow.pythonanywhere.com/\n\n"
        "Выберите действие:"
    )

    update.message.reply_text(admin_text, parse_mode='HTML', reply_markup=reply_markup)

# Обработка сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ У вас нет доступа к этой функции.")
        return

    text = update.message.text

    if text == "📊 Статистика":
        update.message.reply_text("📊 Перейдите в веб-интерфейс для просмотра статистики:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")
    elif text == "👥 Пользователи":
        update.message.reply_text("👥 Управление пользователями в веб-интерфейсе:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")
    elif text == "🎁 Выдать токены":
        update.message.reply_text("🎁 Используйте веб-интерфейс для выдачи токенов:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")
    elif text == "⚙️ Настройки":
        update.message.reply_text("⚙️ Все настройки в веб-интерфейсе:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")

# Основная функция
def main() -> None:
    try:
        # Создаем updater
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        # Обработчики команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

        # Запуск бота
        logger.info("🤖 Бот запускается на Replit...")
        updater.start_polling()
        logger.info("✅ Бот успешно запущен!")
        
        # Бесконечный цикл чтобы Replit не останавливал процесс
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
