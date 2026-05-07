from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('perfil/editar/', views.perfil_editar, name='perfil_editar'),
    
    # Admin
    path('gestao/', views.UsuarioListView.as_view(), name='lista_usuarios'),
    path('gestao/editar/<uuid:pk>/', views.UsuarioUpdateView.as_view(), name='admin_editar_usuario'),
]
