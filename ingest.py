import os
from langchain.text_splitter import CharacterTextSplitter
# --- НОВЫЕ ИМПОРТЫ ---
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = "data"
CHROMA_PATH = "chroma"

def main():
    print("Запуск процесса загрузки данных...")
    
    # --- ОБНОВЛЕННАЯ ЛОГИКА ЗАГРУЗКИ ---
    documents = []
    # Проходим по всем файлам в папке data
    for filename in os.listdir(DATA_PATH):
        file_path = os.path.join(DATA_PATH, filename)
        if filename.endswith('.pdf'):
            # Для PDF используем PyPDFLoader
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
            print(f"Загружен PDF: {filename}")
        elif filename.endswith('.txt'):
            # Для TXT используем TextLoader
            loader = TextLoader(file_path, encoding='utf-8')
            documents.extend(loader.load())
            print(f"Загружен TXT: {filename}")

    print(f"Всего загружено {len(documents)} страниц/документов.")

    # 2. Разделение документов на чанки (без изменений)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Документы разделены на {len(chunks)} чанков.")

    # 3. Создание эмбеддингов и сохранение в ChromaDB (без изменений)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH
    )
    vectorstore.persist()
    
    print("Данные успешно загружены и сохранены в ChromaDB.")


if __name__ == "__main__":
    main()