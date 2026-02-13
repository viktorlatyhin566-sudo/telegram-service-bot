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
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPERATOR_CHAT_ID = int(os.getenv("OPERATOR_CHAT_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения Railway!")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# Состояния
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
    CARTRIDGE_CARTRIDGE_MODEL, CARTRIDGE_ADDRESS, CARTRIDGE_CONFIRM
) = range(20, 27)

# ==========================
# Клавиатуры
# ==========================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠️ Подать заявку на ремонт", callback_data="repair")],
        [InlineKeyboardButton("🚚 Вызвать курьера", callback_data="courier")],
        [InlineKeyboardButton("🖨️ Заправка картриджей", callback_data="cartridge")],
        [InlineKeyboardButton("💻 Помощь системного администратора", callback_data="sysadmin")],
        [InlineKeyboardButton("📍 Адрес и график работы", callback_data="contacts")],
        [InlineKeyboardButton("💬 Связаться с оператором", callback_data="manager")],
        [InlineKeyboardButton("📢 Наши каналы и магазин", callback_data="social")],
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])

def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

# ==========================
# Главное меню
# ==========================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text="👋 Добро пожаловать! Чем поможем? 😊"):
    markup = main_menu_keyboard()
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

# ==========================
# Отмена
# ==========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🚫 Действие отменено.")
    await main_menu(update, context, "Вернулись в главное меню 😊")
    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# Адрес и график
# ==========================
async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🏢 Адрес: г. Днепр, ул. Княгини Ольги, 1 (2-й этаж)\n"
        "🕒 График: Пн–Пт 9:00–18:00, Сб 10:00–15:00\n"
        "📞 067 319 39 96\n"
        "💬 @trablnet\n"
        "✉️ office@kompomir.com"
    )
    kb = [[InlineKeyboardButton("⬅️ В меню", callback_data="main")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ==========================
# Наши каналы и магазин
# ==========================
async def social_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "📢 Наши ресурсы:\n\n"
        "• Канал — @trablnet\n"
        "• Магазин — https://trablnet.com.ua 🛒"
    )
    kb = [[InlineKeyboardButton("⬅️ В меню", callback_data="main")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ==========================
# Оператор
# ==========================
async def manager_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "✍️ Напишите сообщение — оператор ответит максимально быстро 😊",
        reply_markup=cancel_keyboard()
    )
    context.user_data["chat_with_manager"] = True

async def forward_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("chat_with_manager"):
        user = update.message.from_user
        text = f"💬 От {user.first_name} (@{user.username or 'нет'}):\n\n{update.message.text}"
        await context.bot.send_message(OPERATOR_CHAT_ID, text)
        await update.message.reply_text("✅ Отправлено! Скоро ответим 😊", reply_markup=main_menu_keyboard())
        context.user_data["chat_with_manager"] = False

# ==========================
# Общий старт для ремонта и sysadmin
# ==========================
async def repair_or_sysadmin_start(update: Update, context: ContextTypes.DEFAULT_TYPE, is_sysadmin=False) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["is_sysadmin"] = is_sysadmin
    title = "💻 Помощь системного администратора" if is_sysadmin else "🛠️ Запись на ремонт"
    await query.message.reply_text(f"{title}\n\n👤 Введите ваше имя:", reply_markup=cancel_keyboard())
    return REPAIR_NAME

# Остальные шаги ремонта / sysadmin (name, phone, type, brand, model, problem, confirm)
# Здесь нужно вставить функции name_step, phone_step и т.д. из твоей предыдущей рабочей версии

# ==========================
# Курьер
# ==========================
async def courier_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚚 Вызов курьера\n\n👤 Введите ваше имя:", reply_markup=cancel_keyboard())
    return COURIER_NAME

# ... (courier_name, courier_phone, courier_type, courier_brand, courier_model, courier_dimensions, courier_address, courier_confirm)

# ==========================
# Картриджи
# ==========================
async def cartridge_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🖨️ Заправка картриджей\n\n👤 Введите ваше имя:", reply_markup=cancel_keyboard())
    return CARTRIDGE_NAME

# ... (cartridge_name, cartridge_phone, cartridge_brand, cartridge_model, cartridge_cartridge_model, cartridge_address, cartridge_confirm)

# ==========================
# ЗАПУСК
# ==========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Общие
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: main_menu(u, c), pattern="^main$"))

    # Статические
    app.add_handler(CallbackQueryHandler(contacts_handler, pattern="^contacts$"))
    app.add_handler(CallbackQueryHandler(social_handler, pattern="^social$"))
    app.add_handler(CallbackQueryHandler(manager_handler, pattern="^manager$"))

    # Ремонт + Sysadmin
    repair_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(lambda u, c: repair_or_sysadmin_start(u, c, False), pattern="^repair$"),
            CallbackQueryHandler(lambda u, c: repair_or_sysadmin_start(u, c, True), pattern="^sysadmin$"),
        ],
        states={
            REPAIR_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, name_step)],
            REPAIR_PHONE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_step)],
            REPAIR_TYPE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, type_step)],
            REPAIR_BRAND:    [MessageHandler(filters.TEXT & ~filters.COMMAND, brand_step)],
            REPAIR_MODEL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, model_step)],
            REPAIR_PROBLEM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_step)],
            REPAIR_CONFIRM:  [CallbackQueryHandler(confirm_step, pattern="^(confirm|cancel)$")],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
        conversation_timeout=900,
    )
    app.add_handler(repair_conv)

    # Курьер
    courier_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(courier_start, pattern="^courier$")],
        states={
            COURIER_NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_name)],
            COURIER_PHONE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_phone)],
            COURIER_TYPE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_type)],
            COURIER_BRAND:     [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_brand)],
            COURIER_MODEL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_model)],
            COURIER_DIMENSIONS:[MessageHandler(filters.TEXT & ~filters.COMMAND, courier_dimensions)],
            COURIER_ADDRESS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, courier_address)],
            COURIER_CONFIRM:   [CallbackQueryHandler(courier_confirm, pattern="^(confirm|cancel)$")],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
        conversation_timeout=900,
    )
    app.add_handler(courier_conv)

    # Картриджи
    cartridge_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cartridge_start, pattern="^cartridge$")],
        states={
            CARTRIDGE_NAME:           [MessageHandler(filters.TEXT & ~filters.COMMAND, cartridge_name)],
            CARTRIDGE_PHONE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, cartridge_phone)],
            CARTRIDGE_BRAND:          [MessageHandler(filters.TEXT & ~filters.COMMAND, cartridge_brand)],
            CARTRIDGE_MODEL:          [MessageHandler(filters.TEXT & ~filters.COMMAND, cartridge_model)],
            CARTRIDGE_CARTRIDGE_MODEL:[MessageHandler(filters.TEXT & ~filters.COMMAND, cartridge_cartridge)],
            CARTRIDGE_ADDRESS:        [MessageHandler(filters.TEXT & ~filters.COMMAND, cartridge_address)],
            CARTRIDGE_CONFIRM:        [CallbackQueryHandler(cartridge_confirm, pattern="^(confirm|cancel)$")],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
        conversation_timeout=900,
    )
    app.add_handler(cartridge_conv)

    # Сообщения оператору
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_manager))

    # Старт
    app.add_handler(CommandHandler("start", lambda u, c: main_menu(u, c)))

    logger.info("Бот запущен 🚀")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
