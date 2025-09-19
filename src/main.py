import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

# --- НОВЫЕ ИМПОРТЫ ДЛЯ AI ---
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHROMA_PATH = "chroma" # Путь к нашей базе знаний

# --- ИНИЦИАЛИЗАЦИЯ AI-ЛОГИКИ (ПРИ СТАРТЕ БОТА) ---

# 1. Создаем шаблон промпта
# Мы даем модели инструкцию и указываем, куда подставлять контекст и вопрос
PROMPT_TEMPLATE = """
Отвечай на вопрос только на основе следующего контекста:

{context}

---

Ответь на вопрос на основе контекста выше: {question}
"""
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

# 2. Подключаемся к существующей базе данных Chroma
# и создаем "ретривер" - объект, который умеет извлекать из нее данные
embedding_function = OpenAIEmbeddings()
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
retriever = vectorstore.as_retriever()

# 3. Инициализируем языковую модель
llm = ChatOpenAI()

# 4. Собираем все в единую цепочку (RAG chain)
# Это "конвейер", по которому проходит запрос пользователя
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- КОНЕЦ БЛОКА ИНИЦИАЛИЗАЦИИ AI ---


# Создаем веб-сервер и приложение бота
app = FastAPI()
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()


# --- ОБНОВЛЕННЫЕ ОБРАБОТЧИКИ КОМАНД ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start."""
    welcome_text = "Привет! Я AI-консьерж по Батуми. Я знаю немного о ВНЖ и регистрации ИП. Задай мне свой вопрос."
    await update.message.reply_text(welcome_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает обычные текстовые сообщения с помощью RAG."""
    if not update.message or not update.message.text:
        return
    
    user_question = update.message.text
    
    # Отправляем вопрос в нашу RAG-цепочку и получаем ответ
    ai_response = rag_chain.invoke(user_question)
    
    await update.message.reply_text(ai_response)

# --- КОД ДЛЯ ЗАПУСКА СЕРВЕРА (БЕЗ ИЗМЕНЕНИЙ) ---

@app.on_event("startup")
async def startup():
    await application.initialize()
    await application.start()
    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL not set in .env file")
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"Webhook set to {WEBHOOK_URL}/webhook")

@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        update_data = await request.json()
        update = Update.de_json(data=update_data, bot=application.bot)
        await application.update_queue.put(update)
    except Exception as e:
        print(f"Error processing update: {e}")
    return {"status": "ok"}

@app.on_event("shutdown")
async def shutdown():
    await application.stop()
    await application.bot.delete_webhook()
    print("Webhook deleted.")

application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))