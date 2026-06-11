from django.urls import path
from . import views

urlpatterns = [
    path('livro/<uuid:livro_id>/', views.recomendacoes_livro,     name='recomendacoes_livro'),
    path('para-voce/',             views.recomendacoes_para_voce,  name='recomendacoes_para_voce'),
]
