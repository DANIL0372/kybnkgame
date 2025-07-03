import logging
from telegram import Bot
from telegram.ext import Application, CommandHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8131382951:AAEYbYjhBod6_iETzK-qGeiKvhDnVnjy10w"  # Получите у @BotFather


async def start(update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Привет, {user.mention_html()}!\n"
        "Kybnk show разработали свою игру-кликер прямо в телеграме\n\n"
        "🎮 Чтобы начать играть, нажми кнопку 'Открыть игру' в меню бота!\n"
        "💰 Кликай по монете, зарабатывай очки и улучшай свой аккаунт!"
    )
    # Установка кнопки меню после команды /start
    await setup_menu(context.bot)


async def setup_menu(bot: Bot):
    """Настройка меню с кнопкой для открытия игры"""
    await bot.set_chat_menu_button(
        menu_button={
            "type": "web_app",
            "text": "🎮 Открыть игру",
            #"web_app": {"url": "https://ваш-домен.kybnkshow.ru/webapp"}  # Замените на ваш URL
            "web_app": {"url": "https://kybnkshow.ru/"}  # Для локального сервера
        }
    )


def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()