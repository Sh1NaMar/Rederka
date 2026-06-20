# import groq
from groq import Groq
import json
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)


# client = groq.Client(api_key=settings.GROQ_API_KEY)

def generate_prompt_from_scene(scene_text, characters, locations, style="реалистичный"):
    char_desc = "\n".join([f"- {c.name}: {c.context_description}" for c in characters])
    loc_desc = "\n".join([f"- {l.name}: {l.context_description}" for l in locations])

    system_msg = (
        "Ты — помощник визуализатора. Напиши подробный промпт для нейросети, которая генерирует изображения. "
        "Опиши сцену, персонажей, окружение, освещение, настроение и стиль. "
        "Формат: только текст промпта, без лишних комментариев.")
    user_msg = (
        f"Сцена:\n{scene_text}\n\n"
        f"Персонажи:\n{char_desc}\n\n"
        f"Локации:\n{loc_desc}\n\n"
        f"Стиль: {style}\n"
        "Дай промпт на английском языке."
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


def analyze_book_for_scenes(book_text):
    system_msg = (
        "Ты — редактор. Из предоставленного текста выдели ключевые сцены, достойные иллюстрации. "
        "Верни строго JSON-массив объектов с полями order (int) и description (str, сам текст сцены). "
        "Не добавляй ничего лишнего. Только массив JSON."
    )
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": book_text[:15000]},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=2000,
    )
    content = response.choices[0].message.content.strip()

    # Выведем в лог, что пришло (для отладки)
    print(f"Groq raw response: {content}")

    # Убираем возможную обёртку ```json ... ```
    if content.startswith("```"):
        # Удаляем открывающие ``` и всё до конца строки (слово json)
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]
        # Удаляем закрывающие ```
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    # Пытаемся распарсить
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Возможно, ответ пустой или невалидный
        print(f"Failed to parse JSON from: {content}")
        # Можно вернуть пустой список, чтобы задача не падала, но лучше пробросить ошибку с сообщением
        raise ValueError(f"Groq не вернул корректный JSON. Ответ: {content}")


def summarize_page(page_text):
    system_msg = (
        "Ты — литературный критик. Сделай краткий, но информативный конспект страницы книги. "
        "Выдели ключевые события, персонажей, их действия, важные диалоги и локации. "
        "Ответ должен быть на русском языке, объёмом 3–5 предложений."
    )
    user_msg = f"Текст страницы:\n{page_text}"

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.4,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

def analyze_book_for_scenes_from_summaries(summaries):
    combined = "\n\n".join(summaries)
    return analyze_book_for_scenes(combined)  # используем старую функцию с ограничением по длине
