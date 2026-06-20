from django.contrib import admin
from .models import Book, Character, Location, Scene, UserBookProgress, Bookmark, Page, Favorite

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at')
    search_fields = ('title',)

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'book')
    search_fields = ('name',)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'book')
    search_fields = ('name',)

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('book', 'order', 'description')
    filter_horizontal = ('characters', 'locations')

@admin.register(UserBookProgress)
class UserBookProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'percent_read')

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'scene', 'created_at')

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('book', 'number', 'created_at')
    search_fields = ('book__title',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'scene', 'created_at')
    list_filter = ('user',)