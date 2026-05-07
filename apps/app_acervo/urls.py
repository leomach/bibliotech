from django.urls import path
from . import views

urlpatterns = [
    path('', views.LivroListView.as_view(), name='lista_livros'),
    path('cadastrar/', views.cadastrar_livro, name='cadastrar_livro'),
]
