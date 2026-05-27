import time
from django.utils import timezone
from .models import Notificacao

def criar_notificacao(usuario, tipo, mensagem):
    Notificacao.objects.create(usuario=usuario, tipo=tipo, mensagem=mensagem)

def verificar_prazos(usuario):
    """
    Verifica os empréstimos ativos do usuário e cria notificações de prazo/atraso.
    """
    from app_emprestimos.models import Emprestimo
    hoje = timezone.now().date()
    
    # Empréstimos ativos do usuário
    emprestimos = Emprestimo.objects.filter(usuario=usuario, status='ativo')
    
    for emprestimo in emprestimos:
        dias_restantes = (emprestimo.data_prazo - hoje).days
        
        # Caso 1: Prazo se aproximando (2 dias ou menos, mas não atrasado)
        if 0 <= dias_restantes <= 2:
            tipo = 'prazo_proximo'
            mensagem = f"Lembrete: devolva **{emprestimo.exemplar.livro.titulo}** até {emprestimo.data_prazo.strftime('%d/%m/%Y')} ({dias_restantes} dias)."
            
            # Evita duplicar notificação no mesmo dia
            if not Notificacao.objects.filter(
                usuario=usuario, 
                tipo=tipo, 
                mensagem__contains=emprestimo.exemplar.livro.titulo,
                criada_em__date=hoje
            ).exists():
                criar_notificacao(usuario, tipo, mensagem)
        
        # Caso 2: Empréstimo em atraso
        elif dias_restantes < 0:
            tipo = 'emprestimo_atrasado'
            mensagem = f"Seu empréstimo de **{emprestimo.exemplar.livro.titulo}** está atrasado desde {emprestimo.data_prazo.strftime('%d/%m/%Y')}."
            
            # Evita duplicar notificação no mesmo dia
            if not Notificacao.objects.filter(
                usuario=usuario, 
                tipo=tipo, 
                mensagem__contains=emprestimo.exemplar.livro.titulo,
                criada_em__date=hoje
            ).exists():
                criar_notificacao(usuario, tipo, mensagem)
