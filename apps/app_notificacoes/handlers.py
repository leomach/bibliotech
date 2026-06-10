from .services import criar_notificacao

def on_emprestimo_aprovado(sender, emprestimo, **kwargs):
    criar_notificacao(
        usuario=emprestimo.usuario,
        tipo='emprestimo_aprovado',
        mensagem=(
            f"Seu empréstimo de **{emprestimo.exemplar.livro.titulo}** foi aprovado. "
            f"Devolva até {emprestimo.data_prazo.strftime('%d/%m/%Y')}."
        ),
    )

def on_emprestimo_rejeitado(sender, usuario, titulo_livro, **kwargs):
    criar_notificacao(
        usuario=usuario,
        tipo='emprestimo_rejeitado',
        mensagem=f"Seu pedido de empréstimo de **{titulo_livro}** foi recusado.",
    )

def on_devolucao_registrada(sender, emprestimo, titulo_livro, **kwargs):
    criar_notificacao(
        usuario=emprestimo.usuario,
        tipo='devolucao_registrada',
        mensagem=f"Devolução de **{titulo_livro}** registrada. Obrigado!",
    )

def on_livro_disponivel_fila(sender, usuario, titulo_livro, **kwargs):
    criar_notificacao(
        usuario=usuario,
        tipo='livro_disponivel',
        mensagem=f"**{titulo_livro}** está disponível! Solicite seu empréstimo em breve.",
    )

def on_fila_avancou(sender, usuario, titulo_livro, nova_posicao, **kwargs):
    criar_notificacao(
        usuario=usuario,
        tipo='fila_avanco',
        mensagem=f"Você avançou na fila de **{titulo_livro}**. Posição atual: {nova_posicao}.",
    )
