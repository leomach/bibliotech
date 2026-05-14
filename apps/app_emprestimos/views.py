from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Emprestimo, FilaEspera
from app_acervo.models import Livro, Exemplar

@login_required
def solicitar_emprestimo(request, exemplar_id):
    exemplar = get_object_or_404(Exemplar, id=exemplar_id)
    
    if exemplar.status != 'disponivel':
        messages.error(request, "Este exemplar não está disponível para solicitação.")
        return redirect('detalhe_livro', pk=exemplar.livro.pk)

    if Emprestimo.objects.filter(usuario=request.user, exemplar__livro=exemplar.livro, status='pendente').exists():
        messages.warning(request, "Você já tem uma solicitação pendente para este livro.")
        return redirect('detalhe_livro', pk=exemplar.livro.pk)

    try:
        with transaction.atomic():
            exemplar = Exemplar.objects.select_for_update().get(id=exemplar.id)
            if exemplar.status != 'disponivel':
                raise ValueError("Exemplar acabou de ficar indisponível.")

            Emprestimo.objects.create(
                usuario=request.user,
                exemplar=exemplar,
                status='pendente'
            )
            exemplar.status = 'emprestado' 
            exemplar.save()
            messages.success(request, f"Solicitação de '{exemplar.livro.titulo}' enviada!")
    except Exception as e:
        messages.error(request, f"Erro: {str(e)}")

    return redirect('detalhe_livro', pk=exemplar.livro.pk)

@login_required
def validar_emprestimo(request, emprestimo_id):
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id, status='pendente')
    if not request.user.is_bibliotecario and not request.user.is_admin_system:
        messages.error(request, "Acesso negado.")
        return redirect('home')

    if request.method == 'POST':
        acao = request.POST.get('acao')
        try:
            with transaction.atomic():
                if acao == 'aprovar':
                    emprestimo.status = 'ativo'
                    emprestimo.data_emprestimo = timezone.now().date()
                    emprestimo.save()
                    messages.success(request, f"Empréstimo validado!")
                elif acao == 'rejeitar':
                    exemplar = emprestimo.exemplar
                    exemplar.status = 'disponivel'
                    exemplar.save()
                    emprestimo.delete()
                    messages.info(request, "Solicitação rejeitada.")
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}")
            
    return redirect('lista_emprestimos')

@login_required
def remover_da_fila(request, fila_id):
    reserva = get_object_or_404(FilaEspera, id=fila_id)
    if not request.user.is_bibliotecario and not request.user.is_admin_system:
        messages.error(request, "Apenas administradores podem remover pessoas da fila.")
        return redirect('detalhe_livro', pk=reserva.livro.pk)

    livro_pk = reserva.livro.pk
    try:
        with transaction.atomic():
            reserva.delete()
            # Reordenar fila
            restante = FilaEspera.objects.filter(livro_id=livro_pk).order_by('posicao')
            for i, item in enumerate(restante):
                item.posicao = i + 1
                item.save()
            messages.success(request, "Usuário removido da fila.")
    except Exception as e:
        messages.error(request, f"Erro: {str(e)}")
    
    return redirect('detalhe_livro', pk=livro_pk)

@login_required
def realizar_emprestimo(request, exemplar_id):
    exemplar = get_object_or_404(Exemplar, id=exemplar_id)
    if not request.user.is_bibliotecario and not request.user.is_admin_system:
        messages.error(request, "Acesso negado.")
        return redirect('detalhe_livro', pk=exemplar.livro.pk)

    usuario_email = request.POST.get('usuario_email')
    from app_usuarios.models import Usuario
    try:
        usuario_alvo = Usuario.objects.get(email=usuario_email)
        with transaction.atomic():
            exemplar = Exemplar.objects.select_for_update().get(id=exemplar.id)
            Emprestimo.objects.create(usuario=usuario_alvo, exemplar=exemplar, status='ativo')
            exemplar.status = 'emprestado'
            exemplar.save()
            messages.success(request, f"Empréstimo realizado!")
    except Exception as e:
        messages.error(request, f"Erro: {str(e)}")
    return redirect('detalhe_livro', pk=exemplar.livro.pk)

@login_required
def registrar_devolucao(request, emprestimo_id):
    emprestimo = get_object_or_404(Emprestimo, id=emprestimo_id, status='ativo')
    if not request.user.is_bibliotecario and not request.user.is_admin_system:
        return redirect('home')

    try:
        with transaction.atomic():
            emprestimo.status = 'devolvido'
            emprestimo.data_devolucao = timezone.now().date()
            emprestimo.save()
            exemplar = emprestimo.exemplar
            exemplar.status = 'disponivel'
            exemplar.save()
            messages.success(request, f"Devolução registrada.")
            proximo = FilaEspera.objects.filter(livro=exemplar.livro).order_by('posicao').first()
            if proximo:
                messages.info(request, f"Próximo na fila: {proximo.usuario.nome}.")
                proximo.delete()
    except Exception as e:
        messages.error(request, f"Erro: {str(e)}")
    return redirect('lista_emprestimos')

@login_required
def entrar_fila(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    if not FilaEspera.objects.filter(usuario=request.user, livro=livro).exists():
        with transaction.atomic():
            pos = FilaEspera.objects.filter(livro=livro).count() + 1
            FilaEspera.objects.create(usuario=request.user, livro=livro, posicao=pos)
            messages.success(request, f"Entrou na fila! Posição: {pos}")
    return redirect('detalhe_livro', pk=livro.pk)

@login_required
def lista_emprestimos(request):
    if request.user.is_bibliotecario or request.user.is_admin_system:
        q = Emprestimo.objects.filter(status__in=['pendente', 'ativo'])
        if not request.user.is_admin_system:
            q = q.filter(exemplar__livro__biblioteca=request.user.biblioteca)
    else:
        q = Emprestimo.objects.filter(usuario=request.user)
    return render(request, 'emprestimos/lista.html', {'emprestimos': q, 'today': timezone.now().date()})
