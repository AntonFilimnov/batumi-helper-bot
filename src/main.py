# src/main.py
import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHROMA_PATH = "chroma"

chat_histories = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in chat_histories:
        chat_histories[session_id] = ChatMessageHistory()
    return chat_histories[session_id]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Отвечай на вопрос только на основе следующего контекста:\n\n{context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

embedding_function = OpenAIEmbeddings()
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
retriever = vectorstore.as_retriever()
llm = ChatOpenAI()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# --- ИСПРАВЛЕННАЯ RAG-ЦЕПОЧКА ---
rag_chain = (
    {
        "context": itemgetter("question") | retriever | format_docs,
        "question": itemgetter("question"),
        "history": itemgetter("history"), # <-- ВОТ ОНА, НЕДОСТАЮЩАЯ СТРОКА!
    }
    | prompt
    | llm
    | StrOutputParser()
)

conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# --- КОНЕЦ БЛОКА ИНИЦИАЛИЗАЦИИ ---

app = FastAPI()
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_question = update.message.text
    chat_id = str(update.message.chat_id)
    
    # Теперь этот вызов корректен, т.к. наша цепочка ожидает словарь
    ai_response = conversational_rag_chain.invoke(
        {"question": user_question, "history": []}, # Добавляем пустую историю в первый вызов
        config={"configurable": {"session_id": chat_id}}
    )
    
    await update.message.reply_text(ai_response)

# Остальной код без изменений
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "Привет! Я AI-консьерж по Батуми. Я помню наш диалог. Задай мне свой вопрос."
    await update.message.reply_text(welcome_text)

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