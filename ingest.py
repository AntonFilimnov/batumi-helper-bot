import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Загружаем переменные окружения, в первую очередь OpenAI API ключ
load_dotenv()

# Путь к папке с данными и к папке для хранения базы
DATA_PATH = "data"
CHROMA_PATH = "chroma"

def main():
    print("Запуск процесса загрузки данных...")

    # 1. Загрузка документов из папки
    loader = DirectoryLoader(DATA_PATH, glob="*.txt")
    documents = loader.load()
    print(f"Загружено {len(documents)} документов.")

    # 2. Разделение документов на чанки (небольшие куски)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Документы разделены на {len(chunks)} чанков.")

    # 3. Создание эмбеддингов и сохранение в ChromaDB
    # OpenAIEmbeddings будет превращать текст в векторы (числа)
    # Chroma.from_documents создаст базу и сохранит в нее векторы
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH
    )

    # Заставляем базу данных сохраниться на диск
    vectorstore.persist()

    print("Данные успешно загружены и сохранены в ChromaDB.")


if __name__ == "__main__":
    main()