from django import forms
from .models import Scene, Character, Location

class SceneForm(forms.ModelForm):
    characters = forms.ModelMultipleChoiceField(
        queryset=Character.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    locations = forms.ModelMultipleChoiceField(
        queryset=Location.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Scene
        fields = ['order', 'description', 'characters', 'locations']

    def __init__(self, *args, **kwargs):
        book = kwargs.pop('book', None)
        super().__init__(*args, **kwargs)
        if book:
            self.fields['characters'].queryset = Character.objects.filter(book=book)
            self.fields['locations'].queryset = Location.objects.filter(book=book)