import uuid
from django.db import models

class Biblioteca(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    endereco = models.CharField(max_length=255)

    def __str__(self):
        return self.nome
