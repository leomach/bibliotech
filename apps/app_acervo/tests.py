from django.test import TestCase, Client
from django.urls import reverse
from app_usuarios.models import Usuario
from app_bibliotecas.models import Biblioteca
from app_acervo.models import Livro, Exemplar
import uuid

class AcervoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.biblioteca = Biblioteca.objects.create(nome="Biblioteca Central", endereco="Rua A")
        self.biblioteca_outra = Biblioteca.objects.create(nome="Biblioteca Norte", endereco="Rua B")
        
        self.admin = Usuario.objects.create_superuser(
            username="admin@teste.com", 
            email="admin@teste.com", 
            password="password123",
            nome="Admin"
        )
        self.admin.papel = 'admin'
        self.admin.save()
        
        self.bibliotecario = Usuario.objects.create_user(
            username="biblio@teste.com", 
            email="biblio@teste.com", 
            password="password123",
            nome="Bibliotecario",
            papel='bibliotecario',
            biblioteca=self.biblioteca
        )
        
        self.livro = Livro.objects.create(
            isbn="1234567890123",
            titulo="Dom Casmurro",
            autor="Machado de Assis",
            categoria="Clássico",
            biblioteca=self.biblioteca
        )
        
        self.exemplar = Exemplar.objects.create(
            livro=self.livro,
            codigo_barras="BAR123",
            status="disponivel"
        )

    def test_lista_livros(self):
        response = self.client.get(reverse('lista_livros'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dom Casmurro")

    def test_busca_livros(self):
        # Busca por título
        response = self.client.get(reverse('lista_livros'), {'q': 'Dom'})
        self.assertContains(response, "Dom Casmurro")
        
        # Busca que não existe
        response = self.client.get(reverse('lista_livros'), {'q': 'Harry Potter'})
        self.assertNotContains(response, "Dom Casmurro")

    def test_filtro_biblioteca(self):
        response = self.client.get(reverse('lista_livros'), {'biblioteca': self.biblioteca.id})
        self.assertContains(response, "Dom Casmurro")
        
        response = self.client.get(reverse('lista_livros'), {'biblioteca': self.biblioteca_outra.id})
        self.assertNotContains(response, "Dom Casmurro")

    def test_detalhe_livro(self):
        response = self.client.get(reverse('detalhe_livro', kwargs={'pk': self.livro.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dom Casmurro")
        self.assertContains(response, "BAR123")

    def test_cadastrar_livro_bibliotecario(self):
        self.client.login(email="biblio@teste.com", password="password123")
        url = reverse('cadastrar_livro')
        data = {
            'isbn': '9876543210987',
            'titulo': 'O Alienista',
            'autor': 'Machado de Assis',
            'categoria': 'Conto',
            'biblioteca': self.biblioteca.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Redirect to lista_livros
        self.assertTrue(Livro.objects.filter(titulo="O Alienista").exists())
        
        # Verifica se biblioteca foi forçada se o bibliotecário tentasse mudar (embora no form ele possa escolher, a view deve garantir ou o form deve restringir)
        # Na minha view eu fiz: if request.user.is_bibliotecario: livro.biblioteca = request.user.biblioteca
        livro = Livro.objects.get(titulo="O Alienista")
        self.assertEqual(livro.biblioteca, self.biblioteca)

    def test_gerenciar_exemplares_permissao(self):
        # Usuário não logado
        url = reverse('gerenciar_exemplares', kwargs={'pk': self.livro.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirect to login
        
        # Bibliotecário de outra biblioteca
        biblio_norte = Usuario.objects.create_user(
            username="biblio_norte@teste.com", 
            email="biblio_norte@teste.com", 
            password="password123",
            nome="Biblio Norte",
            papel='bibliotecario',
            biblioteca=self.biblioteca_outra
        )
        self.client.login(email="biblio_norte@teste.com", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) # Redirect with error message
        
        # Bibliotecário da biblioteca correta
        self.client.login(email="biblio@teste.com", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
