from django.apps import AppConfig

class AppNotificacoesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_notificacoes'

    def ready(self):
        from django.apps import apps
        if not apps.is_installed('app_emprestimos'):
            return

        from app_emprestimos import signals as emp_signals
        from . import handlers

        emp_signals.emprestimo_aprovado.connect(handlers.on_emprestimo_aprovado)
        emp_signals.emprestimo_rejeitado.connect(handlers.on_emprestimo_rejeitado)
        emp_signals.devolucao_registrada.connect(handlers.on_devolucao_registrada)
        emp_signals.livro_disponivel_fila.connect(handlers.on_livro_disponivel_fila)
        emp_signals.fila_avancou.connect(handlers.on_fila_avancou)
