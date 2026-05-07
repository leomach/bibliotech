from django import forms
from .models import Livro, Exemplar

class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = ['isbn', 'titulo', 'autor', 'categoria', 'biblioteca']
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'autor': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'biblioteca': forms.Select(attrs={'class': 'form-select'}),
        }

class ExemplarForm(forms.ModelForm):
    class Meta:
        model = Exemplar
        fields = ['livro', 'status', 'codigo_barras']
        widgets = {
            'livro': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
        }
