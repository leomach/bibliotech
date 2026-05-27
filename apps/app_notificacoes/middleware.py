import time
from .services import verificar_prazos

class VerificaPrazosMiddleware:
    """Executa no máximo uma vez por hora por usuário."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ultima = request.session.get('ultima_verificacao_prazos', 0)
            agora = time.time()
            # 3600 segundos = 1 hora
            if agora - ultima > 3600:
                verificar_prazos(request.user)
                request.session['ultima_verificacao_prazos'] = agora
        
        response = self.get_response(request)
        return response
