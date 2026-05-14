import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Emprestimo(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente de Validação'),
        ('ativo', 'Ativo'),
        ('devolvido', 'Devolvido'),
        ('atrasado', 'Atrasado'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='emprestimos'
    )
    exemplar = models.ForeignKey(
        'app_acervo.Exemplar', 
        on_delete=models.CASCADE, 
        related_name='historico_emprestimos'
    )
    data_emprestimo = models.DateField(default=timezone.now)
    data_prazo = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    class Meta:
        ordering = ['-data_emprestimo']
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'

    def __str__(self):
        return f"{self.usuario.nome} - {self.exemplar.livro.titulo} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.data_prazo:
            # Padrão de 14 dias conforme o PDF
            self.data_prazo = self.data_emprestimo + timedelta(days=14)
        super().save(*args, **kwargs)

class FilaEspera(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reservas'
    )
    livro = models.ForeignKey(
        'app_acervo.Livro', 
        on_delete=models.CASCADE, 
        related_name='fila_espera'
    )
    posicao = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['posicao']
        unique_together = ('usuario', 'livro')
        verbose_name = 'Fila de Espera'
        verbose_name_plural = 'Filas de Espera'

    def __str__(self):
        return f"{self.posicao}º - {self.usuario.nome} em {self.livro.titulo}"
