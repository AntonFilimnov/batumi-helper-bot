import os
import uvicorn
import telegram
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# --- Загрузка конфигурации ---
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Вставь сюда свой актуальный URL из ngrok!
WEBHOOK_URL = "https://f7bffee77ee0.ngrok-free.app"

# --- "Ручная" база знаний ---
KNOWLEDGE_BASE = {
    "внж": "Для получения ВНЖ в Грузии нужно собрать пакет документов, включая...\n1. Заявление\n2. Копия паспорта\n3. Справка о доходах...",
    "ип": "Регистрация ИП происходит в Доме Юстиции и занимает около 1 дня. Вам понадобится..."
}

# --- Логика бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    await update.message.reply_text("Привет! Я твой помощник по Батуми. Спроси меня про 'ВНЖ' или 'ИП'.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    user_text = update.message.text.lower()
    print(f"User message received: '{user_text}'")

    response = "Извини, я пока не знаю ответа на этот вопрос. Попробуй спросить про 'ВНЖ' или 'ИП'."
    for key in KNOWLEDGE_BASE:
        if key in user_text:
            response = KNOWLEDGE_BASE[key]
            break
    
    print(f"Replying with: '{response}'")
    await update.message.reply_text(response)

# --- Настройка FastAPI и Webhook ---
# Инициализируем приложение Telegram Bot ПЕРЕД запуском FastAPI
application = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .build()
)

# Создаем FastAPI-приложение
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Эта функция выполняется один раз при старте сервера."""
    print("Starting up...")
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # --- ДОБАВЬ ЭТУ СТРОЧКУ ---
    await application.initialize() # <--- ВОТ ОНА, НАША ИНИЦИАЛИЗАЦИЯ
    # --------------------------
    
    # Устанавливаем вебхук
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"Webhook set to {WEBHOOK_URL}/webhook")

@app.on_event("shutdown")
async def shutdown_event():
    """Эта функция выполняется при остановке сервера."""
    print("Shutting down...")
    await application.bot.delete_webhook()

@app.post("/webhook")
async def webhook(request: Request):
    """Эта 'ручка' принимает обновления от Telegram."""
    await application.process_update(
        Update.de_json(data=await request.json(), bot=application.bot)
    )
    return {"status": "ok"}