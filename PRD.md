# PRD — Módulo de Notificações (Bibliotech)

## 1. Objetivo

Implementar um sistema de notificações que informe os usuários sobre eventos relevantes do ciclo de vida de um empréstimo, sem depender de serviços externos, filas de tarefas, ou bibliotecas de terceiros além do que já está no projeto.

---

## 2. Contexto

O projeto já possui:
- Django Messages Framework (mensagens flash por requisição)
- `EMAIL_BACKEND = ConsoleEmailBackend` (emails impressos no terminal)
- Todos os gatilhos de negócio já identificados nas views de `app_emprestimos`

O que falta é persistência das notificações entre requisições e uma maneira de o usuário consultar o histórico de avisos.

---

## 3. Abordagem: Notificações Persistidas no Banco

Em vez de enviar emails reais ou usar WebSockets, as notificações serão **registros no banco de dados** vinculados ao usuário. Um ícone de sino no layout base exibirá a contagem de notificações não lidas. O usuário acessa a lista ao clicar no sino.

Essa abordagem:
- É totalmente Django-nativo (models + views + templates)
- Não exige nenhuma dependência nova
- Funciona com SQLite sem alterações
- É indistinguível, do ponto de vista do usuário, de um sistema de notificações "real"
- Pode ser estendida para email real no futuro apenas trocando o backend

---

## 4. Eventos a Notificar

| # | Evento | Destinatário | Mensagem |
|---|--------|-------------|---------|
| 1 | Empréstimo aprovado pelo bibliotecário | Usuário solicitante | "Seu empréstimo de **{titulo}** foi aprovado. Devolva até {data_prazo}." |
| 2 | Empréstimo rejeitado pelo bibliotecário | Usuário solicitante | "Seu pedido de empréstimo de **{titulo}** foi recusado." |
| 3 | Livro devolvido e usuário avançou na fila | Próximo(s) na fila | "Você avançou na fila de **{titulo}**. Posição atual: {posicao}." |
| 4 | Livro disponível para o primeiro da fila | 1º da fila | "**{titulo}** está disponível! Solicite seu empréstimo em breve." |
| 5 | Prazo de devolução se aproximando (2 dias) | Usuário com empréstimo ativo | "Lembrete: devolva **{titulo}** até {data_prazo} ({dias} dias)." |
| 6 | Empréstimo em atraso | Usuário com empréstimo atrasado | "Seu empréstimo de **{titulo}** está atrasado desde {data_prazo}." |
| 7 | Devolução registrada com sucesso | Usuário que devolveu | "Devolução de **{titulo}** registrada. Obrigado!" |

---

## 5. Modelo de Dados

### App: `app_notificacoes`

```python
class Notificacao(models.Model):
    TIPO_CHOICES = [
        ('emprestimo_aprovado',  'Empréstimo Aprovado'),
        ('emprestimo_rejeitado', 'Empréstimo Rejeitado'),
        ('fila_avanco',          'Avanço na Fila'),
        ('livro_disponivel',     'Livro Disponível'),
        ('prazo_proximo',        'Prazo Próximo'),
        ('emprestimo_atrasado',  'Empréstimo Atrasado'),
        ('devolucao_registrada', 'Devolução Registrada'),
    ]

    id          = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario     = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='notificacoes')
    tipo        = CharField(max_length=30, choices=TIPO_CHOICES)
    mensagem    = TextField()
    lida        = BooleanField(default=False)
    criada_em   = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']
```

Sem FKs para livro/empréstimo — a mensagem já carrega a informação necessária, evitando complexidade de cascades.

---

## 6. Função Auxiliar de Criação

Um único ponto de entrada em `app_notificacoes/services.py`:

```python
def criar_notificacao(usuario, tipo, mensagem):
    Notificacao.objects.create(usuario=usuario, tipo=tipo, mensagem=mensagem)
```

Simples. Sem lógica extra. Quem chama passa os dados prontos.

---

## 7. Gatilhos nas Views Existentes

Os gatilhos são adicionados diretamente às views já existentes em `app_emprestimos/views.py`, chamando `criar_notificacao()` após cada ação:

| View | Evento disparado |
|------|-----------------|
| `validar_emprestimo` (aprovado) | Evento 1 |
| `validar_emprestimo` (rejeitado) | Evento 2 |
| `registrar_devolucao` | Evento 3, 4 e 7 |
| `solicitar_emprestimo` (se havia pendentes na fila) | — |

### Evento 5 e 6 — Verificação Periódica

Como não há Celery nem cron, a verificação de prazos ocorre **a cada requisição autenticada**, dentro de um middleware simples:

```python
class VerificaPrazosMiddleware:
    """Executa no máximo uma vez por hora por usuário."""

    def __call__(self, request):
        if request.user.is_authenticated:
            ultima = request.session.get('ultima_verificacao_prazos', 0)
            agora = time.time()
            if agora - ultima > 3600:
                verificar_prazos(request.user)
                request.session['ultima_verificacao_prazos'] = agora
        return self.get_response(request)
```

`verificar_prazos(usuario)` consulta os empréstimos ativos do usuário e cria notificações de prazo/atraso caso ainda não existam para aquele empréstimo no dia atual.

---

## 8. Interface

### 8.1 Sino no `base.html`

```html
<a href="{% url 'notificacoes:lista' %}">
    🔔
    {% if notificacoes_nao_lidas > 0 %}
        <span class="badge">{{ notificacoes_nao_lidas }}</span>
    {% endif %}
</a>
```

A contagem `notificacoes_nao_lidas` é injetada via **context processor** para ficar disponível em todos os templates sem alterar cada view individualmente.

### 8.2 Página de Notificações

URL: `/notificacoes/`

Lista todas as notificações do usuário logado, mais recentes primeiro. Ao acessar a página, todas são marcadas como lidas.

### 8.3 Marcar como lida via HTMX (opcional)

Um botão por notificação pode marcá-la como lida individualmente com uma requisição HTMX, sem recarregar a página (o projeto já usa `django-htmx`).

---

## 9. Estrutura de Arquivos

```
apps/
└── app_notificacoes/
    ├── __init__.py
    ├── apps.py
    ├── models.py          # Model Notificacao
    ├── services.py        # criar_notificacao(), verificar_prazos()
    ├── views.py           # lista_notificacoes, marcar_lida
    ├── urls.py            # /notificacoes/
    ├── context_processors.py  # injeta contagem no contexto global
    ├── middleware.py      # VerificaPrazosMiddleware
    ├── admin.py
    └── migrations/
        └── 0001_initial.py
```

Templates:
```
templates/
└── notificacoes/
    ├── lista.html
    └── _item.html         # partial para HTMX (marcar lida)
```

---

## 10. Alterações nos Outros Apps

| Arquivo | Alteração |
|---------|-----------|
| `config/settings.py` | Adicionar `app_notificacoes` em `INSTALLED_APPS` e `VerificaPrazosMiddleware` em `MIDDLEWARE` e `context_processors` em `TEMPLATES` |
| `config/urls.py` | Incluir `app_notificacoes.urls` |
| `app_emprestimos/views.py` | Chamar `criar_notificacao()` nos pontos listados na seção 7 |
| `templates/base.html` | Adicionar sino com badge |

---

## 11. O que NÃO será feito

- Envio de e-mail real (backend permanece `ConsoleEmailBackend`)
- WebSockets / Server-Sent Events
- Celery, Redis ou qualquer fila de tarefas
- Novas bibliotecas além das já instaladas
- Notificações push para navegador
- Sistema de preferências de notificação

---

## 12. Critérios de Aceitação

- [ ] Usuário vê contador de notificações não lidas no cabeçalho após login
- [ ] Ao aprovar empréstimo, usuário solicitante recebe notificação
- [ ] Ao rejeitar empréstimo, usuário solicitante recebe notificação
- [ ] Ao registrar devolução, usuário recebe confirmação
- [ ] Ao registrar devolução, próximo(s) na fila recebem notificação de avanço
- [ ] Quando o primeiro da fila recebe notificação de livro disponível
- [ ] Usuário com prazo em 3 dias ou menos recebe lembrete (verificado a cada hora de uso)
- [ ] Usuário com empréstimo atrasado recebe aviso (verificado a cada hora de uso)
- [ ] Ao acessar `/notificacoes/`, todas são marcadas como lidas
- [ ] Nenhuma dependência externa nova introduzida

---

## 13. Estimativa de Implementação

| Tarefa | Esforço estimado |
|--------|-----------------|
| Criar app + model + migration | ~30 min |
| `services.py` (criar + verificar prazos) | ~30 min |
| Context processor + middleware | ~20 min |
| Views + URLs + templates | ~45 min |
| Integrar nas views de empréstimos | ~30 min |
| Ajustar `base.html` + `settings.py` | ~15 min |
| **Total** | **~3 horas** |
