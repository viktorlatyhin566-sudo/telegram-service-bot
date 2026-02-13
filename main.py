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
        [InlineKeyboardButton("🧰 Подать заявку на ремонт", callback_data="repair")],
        [InlineKeyboardButton("🚚 Вызвать курьера", callback_data="courier")],
        [InlineKeyboardButton("🖨 Вызвать заправщика картриджей", callback_data="cartridge")],
        [InlineKeyboardButton("💻 Помощь системного администратора", callback_data="sysadmin")],
        [InlineKeyboardButton("📍 Адрес и график работы", callback_data="contacts")],
        [InlineKeyboardButton("💬 Связаться с оператором", callback_data="manager")],
        [InlineKeyboardButton("📢 Наши боты и группы", callback_data="social")],
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]])

def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить", callback_data="confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

# ==========================
# Главное меню
# ==========================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text="👋 Выберите действие:"):
    markup = main_menu_keyboard()
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

# ==========================
# Общие действия
# ==========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("❌ Действие отменено.")
    await main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# Адрес и график
# ==========================
async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "🏢 Адрес: г. Днепр, ул. Княгини Ольги, дом 1 (2-й этаж)\n"
        "🕒 График: Пн–Пт 9:00–18:00, Сб 10:00–15:00\n"
        "📞 067 319 39 96\n"
        "💬 @trablnet\n"
        "✉️ office@kompomir.com"
    )
    kb = [[InlineKeyboardButton("⬅️ В меню", callback_data="main")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ==========================
# Наши боты и группы
# ==========================
async def social_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "📢 Наши ресурсы:\n\n"
        "• Официальный канал — @trablnet\n"
        "• Интернет-магазин — https://trablnet.com.ua"
    )
    kb = [[InlineKeyboardButton("⬅️ В меню", callback_data="main")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# ==========================
# Связаться с оператором
# ==========================
async def manager_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "✍️ Напишите сообщение — оператор скоро ответит.",
        reply_markup=cancel_keyboard()
    )
    context.user_data["chat_with_manager"] = True

async def forward_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("chat_with_manager"):
        user = update.message.from_user
        text = f"Сообщение оператору от {user.first_name} (@{user.username or 'нет'}):\n\n{update.message.text}"
        await context.bot.send_message(OPERATOR_CHAT_ID, text)
        await update.message.reply_text("✅ Отправлено оператору.", reply_markup=main_menu_keyboard())
        context.user_data["chat_with_manager"] = False

# ==========================
# Общая логика заявок на ремонт / sysadmin
# ==========================
async def repair_or_sysadmin_start(update: Update, context: ContextTypes.DEFAULT_TYPE, is_sysadmin=False) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["is_sysadmin"] = is_sysadmin
    context.user_data["mode"] = "sysadmin" if is_sysadmin else "repair"
    await query.message.reply_text("Введите ваше имя:", reply_markup=cancel_keyboard())
    return REPAIR_NAME

async def name_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Имя не может быть пустым.")
        return REPAIR_NAME
    context.user_data["name"] = text
    await update.message.reply_text("Введите номер телефона:", reply_markup=cancel_keyboard())
    return REPAIR_PHONE

async def phone_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.fullmatch(r"\+?\d{7,15}", text):
        await update.message.reply_text("❗ Неверный формат телефона. Пример: +380671234567")
        return REPAIR_PHONE
    context.user_data["phone"] = text
    await update.message.reply_text("Тип оборудования (ноутбук, ПК, принтер и т.д.):", reply_markup=cancel_keyboard())
    return REPAIR_TYPE

async def type_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["type"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Бренд оборудования:", reply_markup=cancel_keyboard())
    return REPAIR_BRAND

async def brand_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["brand"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Модель оборудования:", reply_markup=cancel_keyboard())
    return REPAIR_MODEL

async def model_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["model"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Опишите проблему:", reply_markup=cancel_keyboard())
    return REPAIR_PROBLEM

async def problem_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["problem"] = update.message.text.strip()
    
    title = "Заявка на помощь системного администратора" if context.user_data.get("is_sysadmin") else "Заявка на ремонт"
    
    summary = (
        f"{title}\n\n"
        f"Имя: {context.user_data.get('name', '—')}\n"
        f"Телефон: {context.user_data.get('phone', '—')}\n"
        f"Тип: {context.user_data.get('type', '—')}\n"
        f"Бренд: {context.user_data.get('brand', '—')}\n"
        f"Модель: {context.user_data.get('model', '—')}\n"
        f"Проблема: {context.user_data.get('problem', '—')}"
    )
    
    await update.message.reply_text(summary + "\n\nВсё верно?", reply_markup=confirm_keyboard())
    return REPAIR_CONFIRM

async def confirm_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data != "confirm":
        await query.message.edit_text("❌ Отменено.")
        await main_menu(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    title = "Заявка на помощь системного администратора" if context.user_data.get("is_sysadmin") else "Заявка на ремонт"
    
    msg = (
        f"{title}\n"
        f"Имя: {context.user_data.get('name', '—')}\n"
        f"Телефон: {context.user_data.get('phone', '—')}\n"
        f"Тип: {context.user_data.get('type', '—')}\n"
        f"Бренд: {context.user_data.get('brand', '—')}\n"
        f"Модель: {context.user_data.get('model', '—')}\n"
        f"Проблема: {context.user_data.get('problem', '—')}"
    )
    
    await context.bot.send_message(OPERATOR_CHAT_ID, msg)
    await query.message.edit_text("✅ Заявка отправлена! Скоро с вами свяжутся.")
    await main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# Курьер
# ==========================
async def courier_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введите ваше имя:", reply_markup=cancel_keyboard())
    return COURIER_NAME

async def courier_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Имя не может быть пустым.")
        return COURIER_NAME
    context.user_data["c_name"] = text
    await update.message.reply_text("Номер телефона:", reply_markup=cancel_keyboard())
    return COURIER_PHONE

async def courier_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.fullmatch(r"\+?\d{7,15}", text):
        await update.message.reply_text("❗ Неверный формат телефона.")
        return COURIER_PHONE
    context.user_data["c_phone"] = text
    await update.message.reply_text("Тип оборудования:", reply_markup=cancel_keyboard())
    return COURIER_TYPE

async def courier_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["c_type"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Бренд:", reply_markup=cancel_keyboard())
    return COURIER_BRAND

async def courier_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["c_brand"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Модель:", reply_markup=cancel_keyboard())
    return COURIER_MODEL

async def courier_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["c_model"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Габариты (если знаете, Д×Ш×В см):", reply_markup=cancel_keyboard())
    return COURIER_DIMENSIONS

async def courier_dimensions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["c_dimensions"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Полный адрес забора:", reply_markup=cancel_keyboard())
    return COURIER_ADDRESS

async def courier_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Адрес обязателен.")
        return COURIER_ADDRESS
    context.user_data["c_address"] = text
    
    summary = (
        "Заявка на вызов курьера\n\n"
        f"Имя: {context.user_data.get('c_name', '—')}\n"
        f"Телефон: {context.user_data.get('c_phone', '—')}\n"
        f"Тип: {context.user_data.get('c_type', '—')}\n"
        f"Бренд: {context.user_data.get('c_brand', '—')}\n"
        f"Модель: {context.user_data.get('c_model', '—')}\n"
        f"Габариты: {context.user_data.get('c_dimensions', '—')}\n"
        f"Адрес: {context.user_data.get('c_address', '—')}"
    )
    await update.message.reply_text(summary + "\n\nВсё верно?", reply_markup=confirm_keyboard())
    return COURIER_CONFIRM

async def courier_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data != "confirm":
        await query.message.edit_text("❌ Отменено.")
        await main_menu(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    msg = (
        "Заявка на вызов курьера\n"
        f"Имя: {context.user_data.get('c_name', '—')}\n"
        f"Телефон: {context.user_data.get('c_phone', '—')}\n"
        f"Тип: {context.user_data.get('c_type', '—')}\n"
        f"Бренд: {context.user_data.get('c_brand', '—')}\n"
        f"Модель: {context.user_data.get('c_model', '—')}\n"
        f"Габариты: {context.user_data.get('c_dimensions', '—')}\n"
        f"Адрес: {context.user_data.get('c_address', '—')}"
    )
    await context.bot.send_message(OPERATOR_CHAT_ID, msg)
    await query.message.edit_text("✅ Заявка отправлена!")
    await main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# Заправка картриджей
# ==========================
async def cartridge_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введите ваше имя:", reply_markup=cancel_keyboard())
    return CARTRIDGE_NAME

async def cartridge_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Имя не может быть пустым.")
        return CARTRIDGE_NAME
    context.user_data["cr_name"] = text
    await update.message.reply_text("Номер телефона:", reply_markup=cancel_keyboard())
    return CARTRIDGE_PHONE

async def cartridge_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not re.fullmatch(r"\+?\d{7,15}", text):
        await update.message.reply_text("❗ Неверный формат телефона.")
        return CARTRIDGE_PHONE
    context.user_data["cr_phone"] = text
    await update.message.reply_text("Бренд принтера / МФУ:", reply_markup=cancel_keyboard())
    return CARTRIDGE_BRAND

async def cartridge_brand(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cr_brand"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Модель принтера / МФУ:", reply_markup=cancel_keyboard())
    return CARTRIDGE_MODEL

async def cartridge_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cr_model"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Модель картриджа (если знаете):", reply_markup=cancel_keyboard())
    return CARTRIDGE_CARTRIDGE_MODEL

async def cartridge_cartridge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cr_cartridge"] = update.message.text.strip() or "не указано"
    await update.message.reply_text("Полный адрес (улица, дом, квартира / частный дом):", reply_markup=cancel_keyboard())
    return CARTRIDGE_ADDRESS

async def cartridge_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("❗ Адрес обязателен.")
        return CARTRIDGE_ADDRESS
    context.user_data["cr_address"] = text
    
    summary = (
        "Заявка на заправку картриджей\n\n"
        f"Имя: {context.user_data.get('cr_name', '—')}\n"
        f"Телефон: {context.user_data.get('cr_phone', '—')}\n"
        f"Бренд принтера: {context.user_data.get('cr_brand', '—')}\n"
        f"Модель принтера: {context.user_data.get('cr_model', '—')}\n"
        f"Модель картриджа: {context.user_data.get('cr_cartridge', '—')}\n"
        f"Адрес: {context.user_data.get('cr_address', '—')}"
    )
    await update.message.reply_text(summary + "\n\nВсё верно?", reply_markup=confirm_keyboard())
    return CARTRIDGE_CONFIRM

async def cartridge_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data != "confirm":
        await query.message.edit_text("❌ Отменено.")
        await main_menu(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    msg = (
        "Заявка на заправку картриджей\n"
        f"Имя: {context.user_data.get('cr_name', '—')}\n"
        f"Телефон: {context.user_data.get('cr_phone', '—')}\n"
        f"Бренд принтера: {context.user_data.get('cr_brand', '—')}\n"
        f"Модель принтера: {context.user_data.get('cr_model', '—')}\n"
        f"Модель картриджа: {context.user_data.get('cr_cartridge', '—')}\n"
        f"Адрес: {context.user_data.get('cr_address', '—')}"
    )
    await context.bot.send_message(OPERATOR_CHAT_ID, msg)
    await query.message.edit_text("✅ Заявка отправлена!")
    await main_menu(update, context)
    context.user_data.clear()
    return ConversationHandler.END

# ==========================
# ЗАПУСК БОТА
# ==========================
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан в переменных окружения!")
        raise ValueError("BOT_TOKEN не задан")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Общие
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: main_menu(u, c), pattern="^main$"))

    # Статические
    app.add_handler(CallbackQueryHandler(contacts_handler, pattern="^contacts$"))
    app.add_handler(CallbackQueryHandler(social_handler, pattern="^social$"))
    app.add_handler(CallbackQueryHandler(manager_handler, pattern="^manager$"))

    # Ремонт / Sysadmin — один ConversationHandler
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

    # Пересылка сообщений оператору
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_manager))

    # Старт
    app.add_handler(CommandHandler("start", lambda u, c: main_menu(u, c)))

    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
