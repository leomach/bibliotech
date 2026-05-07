import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    PAPEL_CHOICES = (
        ('usuario', 'Usuário Comum'),
        ('bibliotecario', 'Bibliotecário'),
        ('admin', 'Administrador'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='usuario')
    biblioteca = models.ForeignKey(
        'app_bibliotecas.Biblioteca', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='usuarios',
        help_text="Obrigatório apenas para Bibliotecários. Usuários comuns podem alugar de várias bibliotecas."
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    # Usaremos email para login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nome']

    def __str__(self):
        return f"{self.nome} ({self.get_papel_display()})"
    
    @property
    def is_bibliotecario(self):
        return self.papel == 'bibliotecario'
    
    @property
    def is_admin_system(self):
        return self.papel == 'admin' or self.is_superuser
