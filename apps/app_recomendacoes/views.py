from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .services import gerar_recomendacoes


@login_required
def recomendacoes_livro(request, livro_id):
    livros = gerar_recomendacoes(request.user, excluir_livro_id=livro_id)
    return render(request, 'recomendacoes/partials/_lista.html', {
        'livros': livros,
        'titulo': 'Você também pode gostar',
    })


@login_required
def recomendacoes_para_voce(request):
    livros = gerar_recomendacoes(request.user)
    return render(request, 'recomendacoes/partials/_lista.html', {
        'livros': livros,
        'titulo': 'Recomendados para você',
    })
