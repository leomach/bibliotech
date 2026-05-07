from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from app_usuarios.permissions import AdminRequiredMixin
from .models import Biblioteca
from .forms import BibliotecaForm

class BibliotecaListView(AdminRequiredMixin, ListView):
    model = Biblioteca
    template_name = 'bibliotecas/lista.html'
    context_object_name = 'bibliotecas'

class BibliotecaCreateView(AdminRequiredMixin, CreateView):
    model = Biblioteca
    form_class = BibliotecaForm
    template_name = 'bibliotecas/form.html'
    success_url = reverse_lazy('lista_bibliotecas')

    def form_valid(self, form):
        messages.success(self.request, "Biblioteca cadastrada com sucesso!")
        return super().form_valid(form)

class BibliotecaUpdateView(AdminRequiredMixin, UpdateView):
    model = Biblioteca
    form_class = BibliotecaForm
    template_name = 'bibliotecas/form.html'
    success_url = reverse_lazy('lista_bibliotecas')

    def form_valid(self, form):
        messages.success(self.request, "Biblioteca atualizada!")
        return super().form_valid(form)
