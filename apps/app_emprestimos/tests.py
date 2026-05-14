from django.test import TestCase, Client
from django.urls import reverse
from app_usuarios.models import Usuario
from app_bibliotecas.models import Biblioteca
from app_acervo.models import Livro, Exemplar
from .models import Emprestimo, FilaEspera
from django.utils import timezone

class EmprestimoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.bib = Biblioteca.objects.create(nome="Bib Central", endereco="Rua 1")
        
        self.biblio = Usuario.objects.create_user(
            username="biblio@teste.com",
            email="biblio@teste.com", 
            password="pass", 
            nome="Biblio",
            papel='bibliotecario',
            biblioteca=self.bib
        )
        
        self.user1 = Usuario.objects.create_user(username="user1@teste.com", email="user1@teste.com", password="pass", nome="User 1")
        self.user2 = Usuario.objects.create_user(username="user2@teste.com", email="user2@teste.com", password="pass", nome="User 2")
        
        self.livro = Livro.objects.create(
            isbn="1", titulo="Livro Teste", autor="Autor", categoria="TI", biblioteca=self.bib
        )
        self.exemplar = Exemplar.objects.create(livro=self.livro, codigo_barras="C1", status='disponivel')

    def test_realizar_emprestimo_sucesso(self):
        self.client.login(email="biblio@teste.com", password="pass")
        url = reverse('realizar_emprestimo', kwargs={'exemplar_id': self.exemplar.id})
        response = self.client.post(url, {'usuario_email': 'user1@teste.com'})
        
        self.assertEqual(response.status_code, 302)
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.status, 'emprestado')
        self.assertTrue(Emprestimo.objects.filter(usuario=self.user1, exemplar=self.exemplar, status='ativo').exists())

    def test_devolucao_e_fila(self):
        # Primeiro, empresta o livro
        self.client.login(email="biblio@teste.com", password="pass")
        self.client.post(reverse('realizar_emprestimo', kwargs={'exemplar_id': self.exemplar.id}), {'usuario_email': 'user1@teste.com'})
        
        # User 2 entra na fila porque não tem exemplar disponível
        self.client.login(email="user2@teste.com", password="pass")
        self.client.post(reverse('entrar_fila', kwargs={'livro_id': self.livro.id}))
        self.assertTrue(FilaEspera.objects.filter(usuario=self.user2, livro=self.livro).exists())
        
        # Bibliotecário registra devolução
        self.client.login(email="biblio@teste.com", password="pass")
        emprestimo = Emprestimo.objects.get(usuario=self.user1, status='ativo')
        self.client.post(reverse('registrar_devolucao', kwargs={'emprestimo_id': emprestimo.id}))
        
        self.exemplar.refresh_from_db()
        self.assertEqual(self.exemplar.status, 'disponivel')
