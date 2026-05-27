from django.urls import path, reverse_lazy
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

    # Password Reset
    path('senha/resetar/', 
         auth_views.PasswordResetView.as_view(
             template_name='usuarios/password_reset_form.html',
             email_template_name='usuarios/password_reset_email.html',
             subject_template_name='usuarios/password_reset_subject.txt',
             success_url=reverse_lazy('password_reset_done')
         ), 
         name='password_reset'),
    path('senha/resetar/enviado/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuarios/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('senha/resetar/confirmar/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuarios/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('senha/resetar/concluido/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuarios/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
