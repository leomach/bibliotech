from django.urls import path
from . import views

urlpatterns = [
    path('', views.BibliotecaListView.as_view(), name='lista_bibliotecas'),
    path('nova/', views.BibliotecaCreateView.as_view(), name='criar_biblioteca'),
    path('editar/<uuid:pk>/', views.BibliotecaUpdateView.as_view(), name='editar_biblioteca'),
]
