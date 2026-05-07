from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from .models import Livro, Exemplar
from .forms import LivroForm

class LivroListView(ListView):
    model = Livro
    template_name = 'acervo/lista_livros.html'
    context_object_name = 'livros'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Livro.objects.filter(
                Q(titulo__icontains=query) | 
                Q(autor__icontains=query) | 
                Q(isbn__icontains=query)
            )
        return Livro.objects.all()

    def get_template_names(self):
        if self.request.htmx:
            return ['acervo/partials/livros_grid.html']
        return ['acervo/lista_livros.html']

@login_required
def cadastrar_livro(request):
    if not request.user.is_bibliotecario and not request.user.is_admin_system:
        messages.error(request, "Acesso negado.")
        return render(request, '403.html', status=403)
    
    if request.method == 'POST':
        form = LivroForm(request.POST)
        if form.is_valid():
            livro = form.save()
            messages.success(request, f"Livro '{livro.titulo}' cadastrado!")
            if request.htmx:
                return render(request, 'acervo/partials/livro_sucesso.html', {'livro': livro})
            return redirect('lista_livros')
        else:
            messages.error(request, "Erro ao cadastrar livro. Verifique os campos.")
    else:
        form = LivroForm()
    
    return render(request, 'acervo/cadastro_livro.html', {'form': form})
