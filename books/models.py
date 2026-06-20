from django.db import models
from django.conf import settings

class Book(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Character(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=200)
    context_description = models.TextField(help_text="Описание персонажа для подстановки в промпт")

    def __str__(self):
        return self.name

class Location(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=200)
    context_description = models.TextField(help_text="Описание локации для подстановки в промпт")

    def __str__(self):
        return self.name

class Scene(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='scenes')
    order = models.IntegerField()
    description = models.TextField(help_text="Текст сцены, отрывок из книги или краткое описание")
    image = models.ImageField(upload_to='scene_images/', blank=True, null=True)
    prompt_used = models.TextField(blank=True)
    characters = models.ManyToManyField('Character', blank=True, related_name='scenes')
    locations = models.ManyToManyField('Location', blank=True, related_name='scenes')

    class Meta:
        ordering = ['order']

class UserBookProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    last_scene = models.ForeignKey(Scene, null=True, blank=True, on_delete=models.SET_NULL)
    percent_read = models.FloatField(default=0)

class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Page(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pages')
    number = models.PositiveIntegerField()
    content = models.TextField()
    summary = models.TextField(blank=True, help_text="Краткий конспект страницы, сгенерированный LLM")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']
        unique_together = ('book', 'number')

    def __str__(self):
        return f"{self.book.title} – стр. {self.number}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'scene')

    def __str__(self):
        return f"{self.user.username} ❤️ {self.scene.book.title} - сцена {self.scene.order}"