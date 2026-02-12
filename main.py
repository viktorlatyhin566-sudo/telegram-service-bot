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
# Пользовательские языки и данные
# ==========================
user_languages = {}
user_data_clear = lambda: {}  # для очистки

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
    CARTRIDGE_CARTRIDGE_MODEL, CARTRIDGE_COUNT, CARTRIDGE_ADDRESS, CARTRIDGE_CONFIRM
) = range(20, 28)

MANAGER_CHAT = 30

# ==========================
# Вспомогательные функции
# ==========================
def check_phone(text: str) -> bool:
    return bool(re.fullmatch(r"\+?\d{7,15}", text.strip()))

def check_not_empty(text: str) -> bool:
    return bool(text.strip())

def check_number(text: str) -> bool:
    return text.strip().isdigit() and int(text.strip()) > 0

def get_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

def get_back_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Назад", callback_data="back"),
         InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

def get_confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить", callback_data="confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

# ==========================
# Главное меню
# ==========================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = "👋 Привет! Выберите действие 👇"):
    keyboard = [
        [InlineKeyboardButton("🧰 Записаться на ремонт", callback_data="repair")],
        [InlineKeyboardButton("🚚 Вызвать курьера", callback_data="courier")],
        [InlineKeyboardButton("🖨 Заправка картриджей", callback_data="cartridge")],
        [InlineKeyboardButton("💬 Связаться с менеджером", callback_data="manager")],
        [InlineKeyboardButton("📍 Адрес и контакты", callback_data="contacts")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# ==========================
# Общие действия
# ==========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.edit_text("❌ Действие отменено.")
    else:
        await update.message.reply_text("❌ Действие отменено.")
    
    context.user_data.clear()
    await main_menu(update, context, "Что дальше?")
    return ConversationHandler.END

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    current_state = context.user_data.get("state", 0)
    if current_state in [REPAIR_PHONE, COURIER_PHONE, CARTRIDGE_PHONE]:
        await query.message.reply_text("Введите ваше имя:")
        return REPAIR_NAME if "repair" in context.user_data.get("mode", "") else \
               COURIER_NAME if "courier" in context.user_data.get("mode", "") else CARTRIDGE_NAME
    
    # Можно расширить "назад" дальше, но для простоты — пока только на имя
    await query.message.reply_text("Вернулись в начало формы. Введите имя:")
    return REPAIR_NAME  # упрощённо

# ==========================
# Подтверждение (общее)
# ==========================
async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, msg: str, state: int):
    await update.message.reply_text(
        f"Проверьте данные:\n\n{msg}\n\nВсё верно?",
        reply_markup=get_confirm_keyboard()
    )
    return state

# ==========================
# Ремонт — Conversation
# ==========================
async def repair_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["mode"] = "repair"
    context.user_data["state"] = REPAIR_NAME
    await query.message.reply_text("Введите ваше имя:", reply_markup=get_cancel_keyboard())
    return REPAIR_NAME

async def repair_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not check_not_empty(update.message.text):
        await update.message.reply_text("❗ Имя не может быть пустым. Введите имя:")
        return REPAIR_NAME
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Введите номер телефона:", reply_markup=get_back_cancel_keyboard())
    return REPAIR_PHONE

# ... (аналогично для остальных шагов ремонта, добавляем reply_markup)

async def repair_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm":
        data = context.user_data
        msg = (
            f"🧾 Новая заявка на ремонт\n"
            f"Имя: {data['name']}\n"
            f"Телефон: {data['phone']}\n"
            f"Тип: {data['type']}\n"
            f"Бренд: {data['brand']}\n"
            f"Модель: {data['model']}\n"
            f"Проблема: {data['problem']}"
        )
        await context.bot.send_message(chat_id=OPERATOR_CHAT_ID, text=msg)
        await query.message.edit_text("✅ Заявка отправлена! Скоро с вами свяжутся.")
        context.user_data.clear()
        await main_menu(update, context)
        return ConversationHandler.END
    
    return await cancel(update, context)

# ==========================
# Запуск бота
# ==========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Общие обработчики
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(CallbackQueryHandler(back, pattern="^back$"))

    # Главное меню и контакты
    app.add_handler(CommandHandler("start", lambda u, c: main_menu(u, c)))
    app.add_handler(CallbackQueryHandler(lambda u, c: main_menu(u, c, "Выберите действие:"), pattern="^main$"))

    # ConversationHandler для ремонта (пример — остальные аналогично)
    repair_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(repair_start, pattern="^repair$")],
        states={
            REPAIR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, repair_name)],
            # ... остальные состояния
            REPAIR_CONFIRM: [CallbackQueryHandler(repair_confirm, pattern="^(confirm|cancel)$")],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
        conversation_timeout=600,  # 10 минут
        name="repair_conversation",
    )
    app.add_handler(repair_conv)

    # Аналогично добавь courier_conv и cartridge_conv

    logger.info("✅ Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
