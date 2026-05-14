from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from .models import Livro, Exemplar
from .forms import LivroForm, ExemplarForm

class LivroListView(ListView):
    model = Livro
    template_name = 'acervo/lista_livros.html'
    context_object_name = 'livros'
    paginate_by = 9

    def get_queryset(self):
        queryset = Livro.objects.all().select_related('biblioteca').prefetch_related('exemplares')
        
        query = self.request.GET.get('q')
        categoria = self.request.GET.get('categoria')
        biblioteca_id = self.request.GET.get('biblioteca')

        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) | 
                Q(autor__icontains=query) | 
                Q(isbn__icontains=query)
            )
        
        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        
        if biblioteca_id:
            queryset = queryset.filter(biblioteca_id=biblioteca_id)
            
        return queryset.order_by('titulo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from app_bibliotecas.models import Biblioteca
        context['bibliotecas'] = Biblioteca.objects.all()
        context['categorias'] = Livro.objects.values_list('categoria', flat=True).distinct()
        return context

    def get_template_names(self):
        if self.request.htmx:
            return ['acervo/partials/livros_grid.html']
        return ['acervo/lista_livros.html']

class LivroDetailView(DetailView):
    model = Livro
    template_name = 'acervo/detalhe_livro.html'
    context_object_name = 'livro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exemplares'] = self.object.exemplares.all()
        context['has_disponivel'] = self.object.exemplares.filter(status='disponivel').exists()
        context['fila_espera'] = self.object.fila_espera.all().order_by('posicao').select_related('usuario')
        return context

@login_required
def cadastrar_livro(request):
    if not request.user.is_bibliotecario and not request.user.is_admin_system:
        messages.error(request, "Acesso negado.")
        return render(request, '403.html', status=403)
    
    if request.user.is_bibliotecario and not request.user.is_admin_system and not request.user.biblioteca:
        messages.error(request, "Você deve estar associado a uma biblioteca para cadastrar livros.")
        return redirect('lista_livros')
    
    if request.method == 'POST':
        form = LivroForm(request.POST)
        if form.is_valid():
            livro = form.save(commit=False)
            if request.user.is_bibliotecario and not request.user.is_admin_system:
                livro.biblioteca = request.user.biblioteca
            livro.save()
            messages.success(request, f"Livro '{livro.titulo}' cadastrado!")
            if request.htmx:
                return render(request, 'acervo/partials/livro_sucesso.html', {'livro': livro})
            return redirect('lista_livros')
        else:
            messages.error(request, "Erro ao cadastrar livro. Verifique os campos.")
    else:
        form = LivroForm()
        if request.user.is_bibliotecario and not request.user.is_admin_system:
            form.fields['biblioteca'].initial = request.user.biblioteca
    
    return render(request, 'acervo/cadastro_livro.html', {'form': form})

@login_required
def gerenciar_exemplares(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    
    if not request.user.is_admin_system:
        if not request.user.is_bibliotecario or request.user.biblioteca != livro.biblioteca:
            messages.error(request, "Você não tem permissão para gerenciar exemplares deste livro.")
            return redirect('detalhe_livro', pk=pk)

    if request.method == 'POST':
        form = ExemplarForm(request.POST)
        if form.is_valid():
            exemplar = form.save(commit=False)
            exemplar.livro = livro
            exemplar.save()
            messages.success(request, "Exemplar adicionado com sucesso!")
            return redirect('detalhe_livro', pk=pk)
    else:
        form = ExemplarForm(initial={'livro': livro})
    
    return render(request, 'acervo/gerenciar_exemplares.html', {
        'form': form,
        'livro': livro
    })

@login_required
def editar_exemplar(request, pk):
    exemplar = get_object_or_404(Exemplar, pk=pk)
    
    if not request.user.is_admin_system:
        if not request.user.is_bibliotecario or request.user.biblioteca != exemplar.livro.biblioteca:
            messages.error(request, "Permissão negada.")
            return redirect('detalhe_livro', pk=exemplar.livro.pk)

    if request.method == 'POST':
        form = ExemplarForm(request.POST, instance=exemplar)
        if form.is_valid():
            form.save()
            messages.success(request, "Exemplar atualizado!")
            return redirect('detalhe_livro', pk=exemplar.livro.pk)
    else:
        form = ExemplarForm(instance=exemplar)
    
    return render(request, 'acervo/editar_exemplar.html', {
        'form': form,
        'exemplar': exemplar
    })

@login_required
def excluir_exemplar(request, pk):
    exemplar = get_object_or_404(Exemplar, pk=pk)
    
    if not request.user.is_admin_system:
        if not request.user.is_bibliotecario or request.user.biblioteca != exemplar.livro.biblioteca:
            messages.error(request, "Permissão negada.")
            return redirect('detalhe_livro', pk=exemplar.livro.pk)

    if request.method == 'POST':
        livro_pk = exemplar.livro.pk
        exemplar.delete()
        messages.success(request, "Exemplar removido do acervo.")
        return redirect('detalhe_livro', pk=livro_pk)
    
    return render(request, 'acervo/excluir_exemplar_confirm.html', {'exemplar': exemplar})

@login_required
def atualizar_status_exemplar(request, pk):
    exemplar = get_object_or_404(Exemplar, pk=pk)
    
    if not request.user.is_admin_system:
        if not request.user.is_bibliotecario or request.user.biblioteca != exemplar.livro.biblioteca:
            messages.error(request, "Permissão negada.")
            return redirect('detalhe_livro', pk=exemplar.livro.pk)

    novo_status = request.POST.get('status')
    if novo_status in dict(Exemplar.STATUS_CHOICES):
        exemplar.status = novo_status
        exemplar.save()
        messages.success(request, f"Status do exemplar {exemplar.codigo_barras} atualizado.")
    
    return redirect('detalhe_livro', pk=exemplar.livro.pk)
