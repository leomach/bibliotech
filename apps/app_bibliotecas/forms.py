from django import forms
from .models import Biblioteca

class BibliotecaForm(forms.ModelForm):
    class Meta:
        model = Biblioteca
        fields = ['nome', 'endereco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
        }
