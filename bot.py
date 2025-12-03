#!/usr/bin/env python3
import sys
import os


# Имитируем модуль imghdr
class ImghdrMock:
    def what(self, file, h=None):
        return "jpeg"


sys.modules['imghdr'] = ImghdrMock()

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
import datetime
import json

# Настройки
BOT_TOKEN = "7730710795:AAFiL2yQyd49Vm7mcUr7idbG1b59jozhGaU"
ADMIN_IDS = [7533352996]

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения состояния рассылки
broadcast_state = {}

# Пути к базам данных
BASE_DIR = os.path.expanduser('~')
NEW_DB_PATH = os.path.join(BASE_DIR, 'kybnk_game.db')


def create_new_database():
    """Создает новую базу данных с улучшенной структурой"""
    try:
        logger.info(f"Создание новой базы данных по пути: {NEW_DB_PATH}")

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
        logger.info(f"✅ Новая база данных создана: {NEW_DB_PATH}")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при создании новой базы данных: {e}")
        return False


def init_db():
    """Инициализация базы данных"""
    try:
        logger.info("🔄 Запуск инициализации базы данных...")

        if create_new_database():
            logger.info("✅ Новая база данных успешно создана")
        else:
            logger.error("❌ Не удалось создать новую базу данных")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        return False


# Команда /start
def start(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    user = update.effective_user

    # Обработка реферальной системы
    referrer_id = None
    if context.args:
        for arg in context.args:
            if arg.startswith('ref_'):
                referrer_id = arg[4:]  # Извлекаем ID пригласившего
                break

    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        # Проверяем существование пользователя
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # Создаем нового пользователя
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

            # Реферальная система: начисляем бонусы
            if referrer_id and referrer_id != user_id:  # Защита от самоприглашения
                # Начисляем 1000 токенов новому пользователю
                cursor.execute('UPDATE users SET balance = balance + 1000 WHERE user_id = ?', (user_id,))

                # Начисляем 2000 токенов пригласившему и увеличиваем счетчик рефералов
                cursor.execute('UPDATE users SET balance = balance + 2000, referrals = referrals + 1 WHERE user_id = ?',
                               (referrer_id,))

                # Отправляем уведомление пригласившему
                try:
                    context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 По вашей реферальной ссылке присоединился: @{user.username or user.first_name or 'новый пользователь'}\n\n"
                             f"💎 Вы получили: 2000 токенов\n"
                             f"🎁 Друг получил: 1000 токенов",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление рефереру {referrer_id}: {e}")

            conn.commit()
            logger.info(f"✅ Создан новый пользователь: {user_id}, реферер: {referrer_id}")
        else:
            logger.info(f"ℹ️ Пользователь уже существует: {user_id}")

        conn.close()
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения пользователя: {e}")

    # Проверяем является ли пользователь администратором
    is_admin = user_id == "7533352996"

    if is_admin:
        show_admin_panel(update, context)
        return

    user_name = user.first_name or "Дорогой пользователь"

    # Формируем реферальную ссылку
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

    update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )


# Команда /restart - сброс прогресса пользователя
def restart_command(update: Update, context: CallbackContext) -> None:
    """Сброс прогресса текущего пользователя"""
    user_id = str(update.effective_user.id)

    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        # Сбрасываем данные пользователя к начальным значениям
        cursor.execute('''
            UPDATE users SET
                balance = 0,
                level = 1,
                level_name = 'Новичок 🟢',
                discount = 0,
                clicks = 0,
                total_earned = 0,
                referrals = 0,
                passive_income = 0,
                upgrades = ?,
                bonuses = ?,
                energy = 100,
                max_energy = 100,
                last_energy_update = ?,
                last_passive_claim = ?,
                boost = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            '{"click_power":1,"passive":0,"autoclick":0,"energy_limit":0}',
            '{"kybnk_show":false,"kybnk_shop":false}',
            int(datetime.datetime.now().timestamp() * 1000),
            int(datetime.datetime.now().timestamp() * 1000),
            '{"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1}',
            user_id
        ))

        conn.commit()
        conn.close()

        update.message.reply_text(
            "✅ Ваш прогресс был сброшен! Вы начинаете с чистого листа.\n\n"
            "Для начала игры перейдите по ссылке:\n"
            "https://kybnkshow.pythonanywhere.com/",
            parse_mode='HTML'
        )

        logger.info(f"🔄 Пользователь {user_id} сбросил свой прогресс")

    except Exception as e:
        logger.error(f"❌ Ошибка при сбросе прогресса: {e}")
        update.message.reply_text("❌ Произошла ошибка при сбросе прогресса.")


# Команда /restart_all - сброс всех пользователей (только для админа)
def restart_all_command(update: Update, context: CallbackContext) -> None:
    """Команда для сброса всех пользователей (только для админа)"""
    user_id = str(update.effective_user.id)

    if user_id != "7533352996":
        update.message.reply_text("❌ У вас нет прав доступа к этой команде.")
        return

    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users SET
                balance = 0,
                level = 1,
                level_name = 'Новичок 🟢',
                discount = 0,
                clicks = 0,
                total_earned = 0,
                referrals = 0,
                passive_income = 0,
                upgrades = ?,
                bonuses = ?,
                energy = 100,
                max_energy = 100,
                last_energy_update = ?,
                last_passive_claim = ?,
                boost = ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (
            '{"click_power":1,"passive":0,"autoclick":0,"energy_limit":0}',
            '{"kybnk_show":false,"kybnk_shop":false}',
            int(datetime.datetime.now().timestamp() * 1000),
            int(datetime.datetime.now().timestamp() * 1000),
            '{"available":true,"lastUsed":0,"active":false,"endTime":0,"cooldownEnd":0,"multiplier":1}'
        ))

        conn.commit()
        count = cursor.rowcount
        conn.close()

        message = f"✅ *Сброшены данные всех пользователей!* ({count} пользователей)\n\nВсе игроки начинают с чистого листа! 🎮"

        update.message.reply_text(message, parse_mode='Markdown')

        logger.info(f"🔄 Админ {user_id} сбросил всех пользователей ({count} чел.)")

    except Exception as e:
        logger.error(f"❌ Ошибка при массовом сбросе: {e}")
        update.message.reply_text("❌ Произошла ошибка при массовом сбросе данных.")


# Команда /admin
def admin_command(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    if user_id != "7533352996":
        update.message.reply_text("❌ У вас нет прав доступа к админ-панели.")
        return

    show_admin_panel(update, context)


# Показать админ-панель
def show_admin_panel(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton("📊 Сегодняшняя статистика"), KeyboardButton("📈 Общая статистика")],
        [KeyboardButton("👥 Управление пользователями"), KeyboardButton("🎁 Выдать токены")],
        [KeyboardButton("⚙️ Настройки бота"), KeyboardButton("📢 Рассылка")],
        [KeyboardButton("🔄 Обновить статистику")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "⚙️ Админ-панель KYBNK кликер\n\n"
        "Доступ к веб-интерфейсу:\n"
        "https://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )


# Обработка текстовых сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    if user_id != "7533352996":
        return

    text = update.message.text

    if text == "📊 Сегодняшняя статистика":
        send_today_stats(update, context)
    elif text == "📈 Общая статистика":
        send_general_stats(update, context)
    elif text == "👥 Управление пользователями":
        update.message.reply_text(
            "👥 Перейдите в веб-интерфейс для управления пользователями:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")
    elif text == "🎁 Выдать токены":
        update.message.reply_text(
            "🎁 Используйте веб-интерфейс для выдачи токенов:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")
    elif text == "⚙️ Настройки бота":
        update.message.reply_text(
            "⚙️ Настройки доступны в веб-интерфейсе:\nhttps://kybnkshow.pythonanywhere.com/admin/users?password=DnK2025")
    elif text == "📢 Рассылка":
        ask_broadcast_message(update, context)
    elif text == "🔄 Обновить статистику":
        update.message.reply_text("✅ Статистика обновлена!")


# Упрощенные функции статистики
def send_today_stats(update: Update, context: CallbackContext) -> None:
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(balance) FROM users")
        total_balance = cursor.fetchone()[0] or 0

        conn.close()

        message = (
            "📊 Сегодняшняя статистика\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"💰 Всего токенов в системе: {total_balance}\n"
            f"📅 Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}"
        )

        update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        update.message.reply_text("❌ Ошибка при получении статистики")


def send_general_stats(update: Update, context: CallbackContext) -> None:
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0] or 0

        cursor.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 5")
        top_users = cursor.fetchall()

        message = (
            "📈 Общая статистика платформы\n\n"
            f"👥 Всего пользователей: {total_users}\n\n"
            "🏆 Топ пользователей:\n"
        )

        for i, (user_id, username, balance) in enumerate(top_users, 1):
            username = username or "Без имени"
            message += f"{i}. {username}: {balance} токенов\n"

        conn.close()
        update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error getting general stats: {e}")
        update.message.reply_text("❌ Ошибка при получении статистики")


# Запрос сообщения для рассылки
def ask_broadcast_message(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    broadcast_state[user_id] = {'waiting': True}

    update.message.reply_text(
        "📢 Создание рассылки\n\n"
        "Введите сообщение для рассылки всем пользователям:"
    )


# Команда reset_link (если нужна)
def reset_link_command(update: Update, context: CallbackContext) -> None:
    """Генерация реферальной ссылки"""
    user_id = str(update.effective_user.id)
    referral_link = f"https://t.me/kybnk_show_bot?start=ref_{user_id}"

    update.message.reply_text(
        f"🔗 Ваша реферальная ссылка:\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"Поделитесь этой ссылкой с друзьями!",
        parse_mode='HTML'
    )


# Основная функция - ИСПРАВЛЕННАЯ ДЛЯ PYTHONANYWHERE
def main() -> None:
    # Инициализация базы данных
    logger.info("🔄 Запуск инициализации базы данных...")
    init_db()

    # ПРОСТАЯ ИНИЦИАЛИЗАЦИЯ ДЛЯ PYTHONANYWHERE
    try:
        # Используем Updater с явным указанием не использовать прокси
        updater = Updater(
            token=BOT_TOKEN,
            use_context=True,
            request_kwargs={'read_timeout': 30, 'connect_timeout': 30}
        )
        dispatcher = updater.dispatcher

        # Обработчики команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("admin", admin_command))
        dispatcher.add_handler(CommandHandler("restart", restart_command))
        dispatcher.add_handler(CommandHandler("restart_all", restart_all_command))
        dispatcher.add_handler(CommandHandler("reset_link", reset_link_command))

        # Обработчики сообщений
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

        # Запуск бота
        logger.info("🤖 Бот запускается...")
        updater.start_polling()
        logger.info("✅ Бот успешно запущен и работает")
        updater.idle()

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")


if __name__ == '__main__':
    main()