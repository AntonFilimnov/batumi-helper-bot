import argparse
from openai import OpenAI
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "chroma"
# Мы больше не передаем OpenAIEmbeddings в Chroma, так как будем работать с векторами напрямую
# embedding_function = OpenAIEmbeddings() 

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="Текст запроса для поиска в базе.")
    args = parser.parse_args()
    query_text = args.query_text

    # --- ШАГ 1: Создаем эмбеддинг для запроса ВРУЧНУЮ ---
    # Используем метод, который, как мы знаем, работает
    print("--- Создаем эмбеддинг для запроса напрямую через OpenAI... ---")
    client = OpenAI()
    response = client.embeddings.create(
        input=query_text,
        model="text-embedding-ada-002"
    )
    query_embedding = response.data[0].embedding
    print("--- Эмбеддинг для запроса успешно создан. ---")

    # --- ШАГ 2: Подключаемся к базе и ищем ПО ВЕКТОРУ ---
    print("--- Подключаемся к ChromaDB и ищем по вектору... ---")
    db = Chroma(persist_directory=CHROMA_PATH) # Подключаемся без embedding_function

    # Используем другой метод поиска, который принимает готовый вектор
    results = db.similarity_search_by_vector_with_relevance_scores(
        embedding=query_embedding, 
        k=3
    )
    print("--- Поиск завершен. ---")

    # --- ШАГ 3: Выводим результаты (без изменений) ---
    if len(results) == 0:
        print("По вашему запросу ничего не найдено.")
        return

    print(f"\n--- Найдено {len(results)} релевантных чанков для запроса: '{query_text}' ---\n")
    for i, (doc, score) in enumerate(results):
        print(f"**Результат #{i + 1} (Сходство: {score:.2f})**")
        print(f"Источник: {doc.metadata.get('source', 'Неизвестно')}")
        print("--------------------------------------------------")
        print(doc.page_content)
        print("\n==================================================\n")


if __name__ == "__main__":
    main()