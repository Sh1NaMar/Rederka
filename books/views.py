import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Max
from .models import Book, Character, Location, Scene, Page, Favorite
from django_q.tasks import async_task
from django_q.models import Success, Failure, OrmQ


# ---------- Книги ----------
@login_required
def book_list(request):
    books = Book.objects.filter(owner=request.user).order_by('-created_at')
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'books/book_list.html', {'page_obj': page_obj})


@login_required
def book_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        if title and content:
            book = Book.objects.create(title=title, content=content, owner=request.user)
            # Разбиение на страницы
            from .utils import split_text_into_pages
            pages_content = split_text_into_pages(book.content)
            for idx, page_content in enumerate(pages_content, start=1):
                Page.objects.create(book=book, number=idx, content=page_content)
            return redirect('book_detail', book_id=book.id)
    return render(request, 'books/book_form.html')


@login_required
def book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})


@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    scenes = book.scenes.all().order_by('order')
    characters = book.characters.all()
    locations = book.locations.all()
    favorite_scene_ids = request.user.favorites.values_list('scene_id', flat=True)
    return render(request, 'books/book_detail.html', {
        'book': book,
        'scenes': scenes,
        'characters': characters,
        'locations': locations,
        'favorite_scene_ids': list(favorite_scene_ids),
    })


# ---------- Чтение книги (без томов) ----------
@login_required
def book_read(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    pages = book.pages.all().order_by('number')
    if not pages.exists():
        from .utils import split_text_into_pages
        chunks = split_text_into_pages(book.content)
        for i, chunk in enumerate(chunks, start=1):
            Page.objects.create(book=book, number=i, content=chunk)
        pages = book.pages.all().order_by('number')
    total_pages = pages.count()
    page_number = request.GET.get('page', 1)
    try:
        page_number = int(page_number)
    except ValueError:
        page_number = 1
    if page_number < 1:
        page_number = 1
    if page_number > total_pages and total_pages > 0:
        page_number = total_pages
    current_page = pages.filter(number=page_number).first()
    if not current_page and total_pages > 0:
        current_page = pages.first()
        page_number = current_page.number if current_page else 1
    scenes = book.scenes.all().order_by('order')
    return render(request, 'books/book_read.html', {
        'book': book,
        'current_page': current_page,
        'page_number': page_number,
        'total_pages': total_pages,
        'scenes': scenes,
    })


# ---------- Сцены ----------
@require_http_methods(["POST"])
@login_required
def start_generation(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id, book__owner=request.user)
    task_id = async_task('books.tasks.generate_scene_illustration', scene_id)
    return JsonResponse({'task_id': task_id})


@require_http_methods(["POST"])
@login_required
def start_all_generations(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    scenes = book.scenes.filter(image='')
    task_ids = []
    for scene in scenes:
        task_id = async_task('books.tasks.generate_scene_illustration', scene.id)
        task_ids.append({'scene_id': scene.id, 'task_id': task_id})
    return JsonResponse({'tasks': task_ids})


@login_required
def check_task(request, task_id):
    success = Success.objects.filter(id=task_id).first()
    if success:
        return JsonResponse({'status': 'SUCCESS', 'result': success.result})
    failure = Failure.objects.filter(id=task_id).first()
    if failure:
        return JsonResponse({'status': 'FAILURE', 'error': str(failure.error)})
    queued = OrmQ.objects.filter(id=task_id).first()
    if queued:
        return JsonResponse({'status': queued.status.upper()})
    return JsonResponse({'status': 'PENDING'}, status=202)


@require_http_methods(["POST"])
@login_required
def analyze_book(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    if book.scenes.exists():
        return JsonResponse({'error': 'Scenes already exist for this book'}, status=400)
    task_id = async_task('books.tasks.analyze_book_for_scenes_task', book_id)
    return JsonResponse({'task_id': task_id})


@require_http_methods(["POST"])
@login_required
def generate_from_selection(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'Текст не может быть пустым'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    max_order = book.scenes.aggregate(Max('order'))['order__max']
    new_order = (max_order or 0) + 1
    scene = Scene.objects.create(
        book=book,
        order=new_order,
        description=text,
        image=None,
        prompt_used=''
    )
    task_id = async_task('books.tasks.generate_scene_illustration', scene.id)
    return JsonResponse({
        'task_id': task_id,
        'scene_id': scene.id,
        'order': new_order
    })


# ---------- Персонажи ----------
@require_http_methods(["POST"])
@login_required
def character_create(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    name = request.POST.get('name')
    description = request.POST.get('context_description')
    if name and description:
        Character.objects.create(book=book, name=name, context_description=description)
    return redirect('book_detail', book_id=book.id)


@login_required
def character_edit(request, pk):
    character = get_object_or_404(Character, pk=pk, book__owner=request.user)
    if request.method == 'POST':
        character.name = request.POST.get('name')
        character.context_description = request.POST.get('context_description')
        character.save()
        return redirect('book_detail', book_id=character.book.id)
    return render(request, 'books/character_form.html', {'character': character})


@login_required
def character_delete(request, pk):
    character = get_object_or_404(Character, pk=pk, book__owner=request.user)
    book_id = character.book.id
    character.delete()
    return redirect('book_detail', book_id=book_id)


# ---------- Локации ----------
@require_http_methods(["POST"])
@login_required
def location_create(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    name = request.POST.get('name')
    description = request.POST.get('context_description')
    if name and description:
        Location.objects.create(book=book, name=name, context_description=description)
    return redirect('book_detail', book_id=book.id)


@login_required
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk, book__owner=request.user)
    if request.method == 'POST':
        location.name = request.POST.get('name')
        location.context_description = request.POST.get('context_description')
        location.save()
        return redirect('book_detail', book_id=location.book.id)
    return render(request, 'books/location_form.html', {'location': location})


@login_required
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk, book__owner=request.user)
    book_id = location.book.id
    location.delete()
    return redirect('book_detail', book_id=book_id)


@login_required
def scene_edit(request, pk):
    scene = get_object_or_404(Scene, pk=pk, book__owner=request.user)
    if request.method == 'POST':
        scene.order = request.POST.get('order')
        scene.description = request.POST.get('description')
        scene.save()
        return redirect('book_detail', book_id=scene.book.id)
    return render(request, 'books/scene_form.html', {
        'scene': scene,
        'book': scene.book  # <-- передаём book в контекст
    })


@login_required
def scene_create(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    if request.method == 'POST':
        order = request.POST.get('order')
        description = request.POST.get('description')
        if order and description:
            Scene.objects.create(book=book, order=order, description=description)
        return redirect('book_detail', book_id=book.id)
    return render(request, 'books/scene_form.html', {'book': book})  # <-- передаём book


@login_required
def scene_delete(request, pk):
    scene = get_object_or_404(Scene, pk=pk, book__owner=request.user)
    book_id = scene.book.id
    scene.delete()
    return redirect('book_detail', book_id=book_id)


@require_http_methods(["POST"])
@login_required
def delete_all_scenes(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    book.scenes.all().delete()
    return redirect('book_detail', book_id=book.id)


# ---------- Добавление страниц (без томов) ----------
@login_required
def add_pages(request, book_id):
    book = get_object_or_404(Book, id=book_id, owner=request.user)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            return render(request, 'books/add_pages.html', {'book': book, 'error': 'Текст не может быть пустым'})
        last_page = book.pages.order_by('-number').first()
        start_number = last_page.number + 1 if last_page else 1
        from .utils import split_text_into_pages
        pages_content = split_text_into_pages(content)
        for idx, page_content in enumerate(pages_content, start=start_number):
            Page.objects.create(book=book, number=idx, content=page_content)
        book.content += "\n\n" + content
        book.save()
        return redirect('book_read', book_id=book.id)
    return render(request, 'books/add_pages.html', {'book': book})


@login_required
def delete_page(request, page_id):
    page = get_object_or_404(Page, id=page_id, book__owner=request.user)
    book_id = page.book.id
    if page.book.pages.count() <= 1:
        # Не даём удалить единственную страницу
        return redirect('book_read', book_id=book_id)
    page.delete()
    return redirect('book_read', book_id=book_id)


# ---------- Избранное ----------
@require_http_methods(["POST"])
@login_required
def toggle_favorite(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id, book__owner=request.user)
    favorite, created = Favorite.objects.get_or_create(user=request.user, scene=scene)
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('scene', 'scene__book').order_by(
        '-created_at')
    return render(request, 'books/favorite_list.html', {'favorites': favorites})


# ---------- Конспект страницы ----------
@require_http_methods(["POST"])
@login_required
def summarize_page(request, page_id):
    page = get_object_or_404(Page, id=page_id, book__owner=request.user)
    if page.summary:
        return JsonResponse({'error': 'Конспект уже существует'}, status=400)
    task_id = async_task('books.tasks.summarize_page_task', page.id)
    return JsonResponse({'task_id': task_id})
