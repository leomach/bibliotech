from django.utils import timezone
from .models import Notificacao

def criar_notificacao(usuario, tipo, mensagem):
    Notificacao.objects.create(usuario=usuario, tipo=tipo, mensagem=mensagem)

def verificar_prazos(usuario):
    from django.apps import apps
    if not apps.is_installed('app_emprestimos'):
        return

    from app_emprestimos.models import Emprestimo
    hoje = timezone.now().date()

    emprestimos = Emprestimo.objects.filter(usuario=usuario, status='ativo')

    for emprestimo in emprestimos:
        dias_restantes = (emprestimo.data_prazo - hoje).days

        if 0 <= dias_restantes <= 2:
            tipo = 'prazo_proximo'
            mensagem = (
                f"Lembrete: devolva **{emprestimo.exemplar.livro.titulo}** até "
                f"{emprestimo.data_prazo.strftime('%d/%m/%Y')} ({dias_restantes} dias)."
            )
            if not Notificacao.objects.filter(
                usuario=usuario,
                tipo=tipo,
                mensagem__contains=emprestimo.exemplar.livro.titulo,
                criada_em__date=hoje,
            ).exists():
                criar_notificacao(usuario, tipo, mensagem)

        elif dias_restantes < 0:
            tipo = 'emprestimo_atrasado'
            mensagem = (
                f"Seu empréstimo de **{emprestimo.exemplar.livro.titulo}** está atrasado "
                f"desde {emprestimo.data_prazo.strftime('%d/%m/%Y')}."
            )
            if not Notificacao.objects.filter(
                usuario=usuario,
                tipo=tipo,
                mensagem__contains=emprestimo.exemplar.livro.titulo,
                criada_em__date=hoje,
            ).exists():
                criar_notificacao(usuario, tipo, mensagem)
