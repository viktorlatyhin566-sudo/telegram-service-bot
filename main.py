import logging
import re
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)

# ==========================
# Настройки
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "7512974894:AAExp5r09Ow5ri1DTA_Vy1hl44-XZmVjyqI")
OPERATOR_CHAT_ID = int(os.getenv("OPERATOR_CHAT_ID", "1383290607"))

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# Состояния (для всех ConversationHandler)
# ==========================
(
    REPAIR_NAME, REPAIR_PHONE, REPAIR_TYPE, REPAIR_BRAND, REPAIR_MODEL, REPAIR_PROBLEM, REPAIR_CONFIRM
) = range(7)

(
    COURIER_NAME, COURIER_PHONE, COURIER_TYPE, COURIER_BRAND, COURIER_MODEL,
    COURIER_DIMENSIONS, COURIER_ADDRESS, COURIER_CONFIRM
) = range(10, 18)

(
    CARTRIDGE_NAME, CARTRIDGE_PHONE, CARTRIDGE_BRAND, CARTRIDGE_MODEL,
    CARTRIDGE_CARTRIDGE_MODEL, CARTRIDGE_COUNT, CARTRIDGE_ADDRESS, CARTRIDGE_CONFIRM
) = range(20, 28)

MANAGER_CHAT = 30

# ==========================
# Вспомогательные клавиатуры
# ==========================
def get_cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])

def get_back_cancel_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Назад", callback_data="back"),
        InlineKeyboardButton("❌ Отмена", callback_data="cancel")
    ]])

def get_confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить", callback_data="confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧰 Записаться на ремонт", callback_data="repair")],
        [InlineKeyboardButton("🚚 Вызвать курьера", callback_data="courier")],
        [InlineKeyboardButton("🖨 Заправка картриджей", callback_data="cartridge")],
        [InlineKeyboardButton("💬 Связаться с менеджером", callback_data="manager")],
        [InlineKeyboardButton("📍 Адрес и контакты", callback_data="contacts")],
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
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("❌ Действие отменено.")
    context.user_data.clear()
    await main_menu(update, context, "Что дальше?")
    return ConversationHandler.END

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

    keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data="main")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# Связь с менеджером
# ==========================
async def manager_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = "✍️ Напишите ваш вопрос прямо сюда — менеджер скоро ответит."
    keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data="main")]]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["chat_with_manager"] = True

# ==========================
# Простой forward для чата с менеджером
# ==========================
async def forward_to_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("chat_with_manager"):
        user = update.message.from_user
        text = f"Сообщение от {user.first_name} (@{user.username or 'нет'}):\n\n{update.message.text}"
        await context.bot.send_message(chat_id=OPERATOR_CHAT_ID, text=text)
        await update.message.reply_text("✅ Сообщение отправлено менеджеру.")
        context.user_data["chat_with_manager"] = False
        await main_menu(update, context)

# ==========================
# Заглушки для курьера и картриджей (пока только начало)
# ==========================
async def courier_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚚 Вызов курьера (в разработке)\n\nВведите имя:", reply_markup=get_cancel_keyboard())
    context.user_data["mode"] = "courier"
    return COURIER_NAME

async def cartridge_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🖨 Заправка картриджей (в разработке)\n\nВведите имя:", reply_markup=get_cancel_keyboard())
    context.user_data["mode"] = "cartridge"
    return CARTRIDGE_NAME

# ==========================
# Запуск бота
# ==========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Общие обработчики
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(CallbackQueryHandler(contacts_handler, pattern="^contacts$"))
    app.add_handler(CallbackQueryHandler(manager_handler, pattern="^manager$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: main_menu(u, c), pattern="^main$"))

    # Чат с менеджером
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_manager))

    # ConversationHandler — ремонт (можно расширять)
    repair_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(lambda u, c: main_menu(u, c, "Ремонт (в разработке)"), pattern="^repair$")],
        states={},
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
        conversation_timeout=600,
    )
    app.add_handler(repair_conv)

    # Курьер и картриджи — пока заглушки
    app.add_handler(CallbackQueryHandler(courier_start, pattern="^courier$"))
    app.add_handler(CallbackQueryHandler(cartridge_start, pattern="^cartridge$"))

    # Старт
    app.add_handler(CommandHandler("start", lambda u, c: main_menu(u, c)))

    logger.info("✅ Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
