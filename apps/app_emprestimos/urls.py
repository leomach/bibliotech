from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_emprestimos, name='lista_emprestimos'),
    path('solicitar/<uuid:exemplar_id>/', views.solicitar_emprestimo, name='solicitar_emprestimo'),
    path('validar/<uuid:emprestimo_id>/', views.validar_emprestimo, name='validar_emprestimo'),
    path('remover-fila/<uuid:fila_id>/', views.remover_da_fila, name='remover_da_fila'),
    path('realizar/<uuid:exemplar_id>/', views.realizar_emprestimo, name='realizar_emprestimo'),
    path('devolver/<uuid:emprestimo_id>/', views.registrar_devolucao, name='registrar_devolucao'),
    path('entrar-fila/<uuid:livro_id>/', views.entrar_fila, name='entrar_fila'),
]
