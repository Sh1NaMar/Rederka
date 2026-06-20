from django.core.files.base import ContentFile
from .models import Scene, Character, Location, Page
from .services.groq_service import generate_prompt_from_scene, analyze_book_for_scenes, summarize_page
from .services.pollinations_service import generate_image


def generate_scene_illustration(scene_id):
    scene = Scene.objects.select_related('book').get(id=scene_id)
    book = scene.book

    # Берём персонажей и локации, связанные со сценой, если есть
    characters = scene.characters.all()
    if not characters:
        characters = Character.objects.filter(book=book)
    locations = scene.locations.all()
    if not locations:
        locations = Location.objects.filter(book=book)

    prompt = generate_prompt_from_scene(scene.description, characters, locations)
    image_data = generate_image(prompt)

    file_name = f"scene_{scene.id}.png"
    scene.image.save(file_name, ContentFile(image_data))
    scene.prompt_used = prompt
    scene.save()
    return f"Illustration for scene {scene.id} generated."


def analyze_book_for_scenes_task(book_id):
    from .models import Book
    from .services.groq_service import analyze_book_for_scenes

    book = Book.objects.get(id=book_id)
    scenes_data = analyze_book_for_scenes(book.content)
    for item in scenes_data:
        Scene.objects.create(
            book=book,
            order=item['order'],
            description=item['description']
        )
    return f"Created {len(scenes_data)} scenes for book {book.id}."


def summarize_page_task(page_id):
    from .models import Page
    page = Page.objects.get(id=page_id)
    summary = summarize_page(page.content)
    page.summary = summary
    page.save()
    return f"Page {page_id} summarized."
