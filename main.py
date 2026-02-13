import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)

# ==========================
# Настройки
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN", )
OPERATOR_CHAT_ID = int(os.getenv("OPERATOR_CHAT_ID", "1383290607"))

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# Вспомогательные клавиатуры
# ==========================
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧰 Записаться на ремонт", callback_data="repair")],
        [InlineKeyboardButton("🚚 Вызвать курьера", callback_data="courier")],
        [InlineKeyboardButton("🖨 Заправка картриджей", callback_data="cartridge")],
        [InlineKeyboardButton("💬 Связаться с менеджером", callback_data="manager")],
        [InlineKeyboardButton("📍 Адрес и контакты", callback_data="contacts")],
    ])

def get_back_to_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="main")]
    ])

# ==========================
# Главное меню
# ==========================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = "👋 Привет! Выберите действие 👇"):
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())

# ==========================
# Общие действия
# ==========================
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    await main_menu(update, context)

# ==========================
# Контакты
# ==========================
async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🏢 Наш адрес: г. Днепр, ул. Княгини Ольги, дом 1 (2-й этаж)\n"
        "📞 067 319 39 96\n"
        "💬 @trablnet\n"
        "✉️ office@kompomir.com"
    )
    await query.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())

# ==========================
# Связь с менеджером
# ==========================
async def manager_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "✍️ Напишите ваш вопрос прямо сюда — менеджер скоро ответит."
    await query.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    context.user_data["chat_with_manager"] = True

# ==========================
# Записаться на ремонт
# ==========================
async def repair_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "Опишите Вашу проблему. Что у Вас не работает?\n"
        "Оставьте контакты. Мы свяжемся с Вами в ближайшее время."
    )
    await query.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    context.user_data["awaiting_repair_description"] = True

# ==========================
# Вызвать курьера
# ==========================
async def courier_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "Напишите Ваш адрес, контактный телефон, опишите что у Вас не работает."
    await query.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    context.user_data["awaiting_courier_request"] = True

# ==========================
# Заправка картриджей
# ==========================
async def cartridge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "Напишите контактный телефон и опишите проблему, "
        "которая у Вас возникла с картриджем."
    )
    await query.message.edit_text(text, reply_markup=get_back_to_menu_keyboard())
    context.user_data["awaiting_cartridge_request"] = True

# ==========================
# Общий обработчик всех запросов от пользователей
# ==========================
async def handle_user_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text.strip()

    if context.user_data.get("awaiting_repair_description"):
        forward_text = (
            f"Новая заявка на РЕМОНТ\n"
            f"От: {user.first_name} ({user.username or 'без @'})\n"
            f"ID: {user.id}\n"
            f"Сообщение:\n{text}"
        )
        await context.bot.send_message(OPERATOR_CHAT_ID, forward_text)
        await update.message.reply_text(
            "Спасибо! Мы получили ваше сообщение и свяжемся в ближайшее время.",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data["awaiting_repair_description"] = False

    elif context.user_data.get("awaiting_courier_request"):
        forward_text = (
            f"Новая заявка на КУРЬЕРА\n"
            f"От: {user.first_name} ({user.username or 'без @'})\n"
            f"ID: {user.id}\n"
            f"Сообщение:\n{text}"
        )
        await context.bot.send_message(OPERATOR_CHAT_ID, forward_text)
        await update.message.reply_text(
            "Спасибо! Мы получили Ваше сообщение и свяжемся в ближайшее время.",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data["awaiting_courier_request"] = False

    elif context.user_data.get("awaiting_cartridge_request"):
        forward_text = (
            f"Новая заявка на ЗАПРАВКУ КАРТРИДЖЕЙ\n"
            f"От: {user.first_name} ({user.username or 'без @'})\n"
            f"ID: {user.id}\n"
            f"Сообщение:\n{text}"
        )
        await context.bot.send_message(OPERATOR_CHAT_ID, forward_text)
        await update.message.reply_text(
            "Спасибо! Мы получили Ваше сообщение и свяжемся в ближайшее время.",
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data["awaiting_cartridge_request"] = False

    elif context.user_data.get("chat_with_manager"):
        forward_text = (
            f"Сообщение менеджеру от {user.first_name} (@{user.username or 'нет'}):\n\n{text}"
        )
        await context.bot.send_message(OPERATOR_CHAT_ID, forward_text)
        await update.message.reply_text("✅ Сообщение отправлено менеджеру.")
        context.user_data["chat_with_manager"] = False
        await main_menu(update, context)

# ==========================
# Запуск бота
# ==========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Кнопки главного меню
    app.add_handler(CallbackQueryHandler(back_to_main, pattern="^main$"))
    app.add_handler(CallbackQueryHandler(contacts_handler, pattern="^contacts$"))
    app.add_handler(CallbackQueryHandler(manager_handler, pattern="^manager$"))
    app.add_handler(CallbackQueryHandler(repair_handler, pattern="^repair$"))
    app.add_handler(CallbackQueryHandler(courier_handler, pattern="^courier$"))
    app.add_handler(CallbackQueryHandler(cartridge_handler, pattern="^cartridge$"))

    # Обработка всех текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_request))

    # Команда /start
    app.add_handler(CommandHandler("start", lambda u, c: main_menu(u, c)))

    logger.info("✅ Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
