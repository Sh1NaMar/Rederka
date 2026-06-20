from django.urls import path
from . import views

urlpatterns = [
    # Книги
    path('', views.book_list, name='book_list'),
    path('book/create/', views.book_create, name='book_create'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('book/<int:book_id>/delete/', views.book_delete, name='book_delete'),
    path('book/<int:book_id>/read/', views.book_read, name='book_read'),
    path('book/<int:book_id>/scenes/delete-all/', views.delete_all_scenes, name='delete_all_scenes'),

    # Сцены и генерация
    path('api/generate/scene/<int:scene_id>/', views.start_generation, name='start_generation'),
    path('api/generate/all/<int:book_id>/', views.start_all_generations, name='start_all_generations'),
    path('api/task/<str:task_id>/', views.check_task, name='check_task'),
    path('api/analyze/book/<int:book_id>/', views.analyze_book, name='analyze_book'),
    path('api/generate/selection/<int:book_id>/', views.generate_from_selection, name='generate_from_selection'),
    path('api/favorite/toggle/<int:scene_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('api/summarize-page/<int:page_id>/', views.summarize_page, name='summarize_page'),

    # Страницы (добавление и удаление)
    path('book/<int:book_id>/add-pages/', views.add_pages, name='add_pages'),
    path('page/<int:page_id>/delete/', views.delete_page, name='delete_page'),

    # Сцены (CRUD)
    path('book/<int:book_id>/scene/add/', views.scene_create, name='scene_create'),
    path('scene/<int:pk>/edit/', views.scene_edit, name='scene_edit'),
    path('scene/<int:pk>/delete/', views.scene_delete, name='scene_delete'),

    # Персонажи
    path('book/<int:book_id>/character/add/', views.character_create, name='character_create'),
    path('character/<int:pk>/edit/', views.character_edit, name='character_edit'),
    path('character/<int:pk>/delete/', views.character_delete, name='character_delete'),

    # Локации
    path('book/<int:book_id>/location/add/', views.location_create, name='location_create'),
    path('location/<int:pk>/edit/', views.location_edit, name='location_edit'),
    path('location/<int:pk>/delete/', views.location_delete, name='location_delete'),

    # Избранное
    path('favorites/', views.favorite_list, name='favorite_list'),
]