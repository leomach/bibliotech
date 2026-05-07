from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

class PublicUsuarioCreationForm(UserCreationForm):
    """Formulário para auto-cadastro (público). 
    Sempre cria usuários com papel 'usuario' e sem biblioteca fixa."""
    class Meta:
        model = Usuario
        fields = ('nome', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.papel = 'usuario'
        user.username = user.email # Garantindo consistência
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('nome', 'email')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class AdminUsuarioCreationForm(UserCreationForm):
    """Formulário para criação administrativa."""
    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'papel', 'biblioteca')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'papel': forms.Select(attrs={'class': 'form-select'}),
            'biblioteca': forms.Select(attrs={'class': 'form-select'}),
        }

class AdminUsuarioUpdateForm(forms.ModelForm):
    """Formulário para edição administrativa (sem senha)."""
    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'papel', 'biblioteca')
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'papel': forms.Select(attrs={'class': 'form-select'}),
            'biblioteca': forms.Select(attrs={'class': 'form-select'}),
        }

class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = ('nome', 'email', 'papel', 'biblioteca')
