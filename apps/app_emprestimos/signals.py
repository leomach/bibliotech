from django.dispatch import Signal

# Emitido após um empréstimo pendente ser aprovado pelo bibliotecário.
# kwargs: emprestimo (instância de Emprestimo com status já 'ativo')
emprestimo_aprovado = Signal()

# Emitido após um empréstimo pendente ser rejeitado e deletado.
# kwargs: usuario (instância), titulo_livro (str)
emprestimo_rejeitado = Signal()

# Emitido após uma devolução ser registrada.
# kwargs: emprestimo (instância com status 'devolvido'), titulo_livro (str)
devolucao_registrada = Signal()

# Emitido para o primeiro da fila quando o livro fica disponível.
# kwargs: usuario (instância), titulo_livro (str)
livro_disponivel_fila = Signal()

# Emitido para cada pessoa que avança na fila após uma devolução.
# kwargs: usuario (instância), titulo_livro (str), nova_posicao (int)
fila_avancou = Signal()
