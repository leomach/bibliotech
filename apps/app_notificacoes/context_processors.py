from .models import Notificacao

def notificacoes_context(request):
    if request.user.is_authenticated:
        count = Notificacao.objects.filter(usuario=request.user, lida=False).count()
        return {'notificacoes_nao_lidas': count}
    return {'notificacoes_nao_lidas': 0}
