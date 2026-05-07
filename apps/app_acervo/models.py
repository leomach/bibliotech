import uuid
from django.db import models

class Livro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    isbn = models.CharField(max_length=13, unique=True)
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100)
    biblioteca = models.ForeignKey(
        'app_bibliotecas.Biblioteca', 
        on_delete=models.CASCADE, 
        related_name='livros'
    )

    def __str__(self):
        return f"{self.titulo} - {self.autor}"

class Exemplar(models.Model):
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('emprestado', 'Emprestado'),
        ('manutencao', 'Em Manutenção'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    livro = models.ForeignKey(
        Livro, 
        on_delete=models.CASCADE, 
        related_name='exemplares'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='disponivel'
    )
    codigo_barras = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.livro.titulo} ({self.codigo_barras}) - {self.get_status_display()}"
