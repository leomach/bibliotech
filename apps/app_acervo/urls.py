from django.urls import path
from . import views

urlpatterns = [
    path('', views.LivroListView.as_view(), name='lista_livros'),
    path('cadastrar/', views.cadastrar_livro, name='cadastrar_livro'),
    path('<uuid:pk>/', views.LivroDetailView.as_view(), name='detalhe_livro'),
    path('<uuid:pk>/exemplares/', views.gerenciar_exemplares, name='gerenciar_exemplares'),
    path('exemplar/<uuid:pk>/editar/', views.editar_exemplar, name='editar_exemplar'),
    path('exemplar/<uuid:pk>/excluir/', views.excluir_exemplar, name='excluir_exemplar'),
    path('exemplar/<uuid:pk>/status/', views.atualizar_status_exemplar, name='atualizar_status_exemplar'),
]
