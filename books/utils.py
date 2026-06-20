def split_text_into_pages(text, chars_per_page=2000):
    """
    Разбивает текст на страницы примерно по `chars_per_page` символов,
    стараясь не разрывать предложения и абзацы.
    """
    # Простой алгоритм: режем по абзацам, группируем до достижения лимита
    paragraphs = text.split('\n')
    pages = []
    current_page = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > chars_per_page and current_page:
            pages.append('\n'.join(current_page))
            current_page = []
            current_len = 0
        current_page.append(para)
        current_len += para_len + 1  # +1 за перенос строки

    if current_page:
        pages.append('\n'.join(current_page))

    # Если не получилось страниц (например, текст пустой) – создаём пустую
    if not pages:
        pages = ['']

    return pages