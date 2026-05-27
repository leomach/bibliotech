import uuid
from django.db import models
from django.conf import settings

class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('emprestimo_aprovado',  'Empréstimo Aprovado'),
        ('emprestimo_rejeitado', 'Empréstimo Rejeitado'),
        ('fila_avanco',          'Avanço na Fila'),
        ('livro_disponivel',     'Livro Disponível'),
        ('prazo_proximo',        'Prazo Próximo'),
        ('emprestimo_atrasado',  'Empréstimo Atrasado'),
        ('devolucao_registrada', 'Devolução Registrada'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificacoes')
    tipo        = models.CharField(max_length=30, choices=TIPO_CHOICES)
    mensagem    = models.TextField()
    lida        = models.BooleanField(default=False)
    criada_em   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.usuario.email} - {self.get_tipo_display()} - {self.criada_em}"
