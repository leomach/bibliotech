from django.urls import path
from . import views

app_name = 'notificacoes'

urlpatterns = [
    path('', views.lista_notificacoes, name='lista'),
    path('marcar-lida/<uuid:pk>/', views.marcar_lida, name='marcar_lida'),
]
