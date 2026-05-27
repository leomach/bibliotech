from django.contrib import admin
from django.urls import path, include
from app_usuarios.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('usuarios/', include('app_usuarios.urls')),
    path('acervo/', include('app_acervo.urls')),
    path('bibliotecas/', include('app_bibliotecas.urls')),
    path('emprestimos/', include('app_emprestimos.urls')),
    path('notificacoes/', include('app_notificacoes.urls', namespace='notificacoes')),
]
