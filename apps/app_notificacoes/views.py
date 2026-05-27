from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Notificacao

@login_required
def lista_notificacoes(request):
    notificacoes = Notificacao.objects.filter(usuario=request.user)
    
    # Ao acessar a lista, marca todas como lidas (conforme PRD)
    notificacoes.filter(lida=False).update(lida=True)
    
    return render(request, 'notificacoes/lista.html', {'notificacoes': notificacoes})

@login_required
def marcar_lida(request, pk):
    notificacao = get_object_or_404(Notificacao, pk=pk, usuario=request.user)
    notificacao.lida = True
    notificacao.save()
    
    if request.htmx:
        # Se for HTMX, retorna o item atualizado ou nada se quisermos remover
        return render(request, 'notificacoes/partials/_item.html', {'notificacao': notificacao})
    
    return HttpResponse(status=204)
