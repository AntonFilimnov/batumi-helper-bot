import os
from openai import OpenAI
from dotenv import load_dotenv

print("--- 1. Скрипт запущен. Загружаем переменные... ---")
load_dotenv()

try:
    print("--- 2. Создаем клиент OpenAI и отправляем запрос... ---")

    # Создаем клиент, он автоматически подхватит ключ из .env
    client = OpenAI()

    # Тот самый сетевой запрос, который, предположительно, виснет
    response = client.embeddings.create(
        input="test",
        model="text-embedding-ada-002"
    )

    print("\n--- 3. УСПЕШНО! Ответ от OpenAI получен. ---")
    print("Ответ выглядит так (первые 5 чисел вектора):")
    print(response.data[0].embedding[:5])

except Exception as e:
    print("\n--- X. ОШИБКА! Запрос не прошел. ---")
    print(f"Тип ошибки: {type(e).__name__}")
    print(f"Текст ошибки: {e}")
