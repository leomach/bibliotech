# PRD — Sistema de Recomendação Inteligente de Livros (Bibliotech)

---

## 1. Objetivo

Implementar um mecanismo de recomendação de livros personalizado por usuário, baseado no histórico de empréstimos. O sistema deve sugerir títulos relevantes de forma passiva (sem que o usuário precise pedir), aproveitando exclusivamente os dados já existentes no banco — sem dependências externas, APIs de ML ou serviços de terceiros.

---

## 2. Contexto

### 2.1 O problema

Atualmente o usuário chega ao acervo e precisa navegar manualmente pelo catálogo para descobrir novos títulos. Não existe nenhum mecanismo que aproveite o historial de leituras para guiar essa descoberta. Isso reduz o engajamento com a plataforma e o giro do acervo.

### 2.2 O que já existe no projeto

| Dado disponível | Onde está | Como será usado |
|---|---|---|
| Histórico de empréstimos do usuário | `Emprestimo` (usuario → exemplar → livro) | Base primária do algoritmo |
| Categoria do livro | `Livro.categoria` (CharField) | Agrupamento por interesse |
| Autor do livro | `Livro.autor` (CharField) | Afinidade por autoria |
| Status do exemplar | `Exemplar.status` | Indicar disponibilidade no card |
| Popularidade global | contagem de `Emprestimo` por livro | Ranqueamento de relevância |

Toda a inteligência necessária está nos dados relacionais já mapeados. Não é necessário nenhum model novo nem dado externo.

---

## 3. Princípio de Modularidade Adotado no Projeto

Antes de detalhar a implementação, é necessário registrar o padrão arquitetural que rege **todas** as funcionalidades do Bibliotech — incluindo esta.

### 3.1 A regra

> Cada app deve poder ser removida de `INSTALLED_APPS` sem quebrar as demais.

Isso significa que nenhum app pode importar diretamente de outro app no **nível de módulo** (top-level imports). Dependências entre apps são permitidas, mas devem ser declaradas de forma que o Python não falhe ao carregar se a dependência não estiver instalada.

### 3.2 Os dois padrões usados

**Padrão A — Django Signals (para apps que precisam notificar outros)**

O app emissor define sinais em `signals.py` e os dispara nas suas views. O app receptor conecta handlers em `apps.py > ready()`, guardado por `apps.is_installed()`. Nenhum dos dois importa o outro no nível de módulo.

```
app_emprestimos/signals.py   → define Signal()
app_emprestimos/views.py     → signal.send(...)
app_notificacoes/apps.py     → ready() conecta handlers SE app_emprestimos instalado
app_notificacoes/handlers.py → funções puras, sem imports de app_emprestimos
```

Remover `app_notificacoes`: empréstimos continuam funcionando, sinais são emitidos mas não têm receptor.
Remover `app_emprestimos`: notificações continuam carregando, `ready()` não conecta nada.

**Padrão B — URL lookup condicional nos templates (para features opcionais de UI)**

Em vez de `{% url 'nome' %}` (que lança `NoReverseMatch` se a URL não existir), usar a forma silenciosa:

```html
{% url 'nome_da_url' arg as variavel %}
{% if variavel %}
    <!-- renderiza apenas se a URL existir -->
{% endif %}
```

Quando a app é removida e suas URLs saem de `config/urls.py`, `variavel` fica vazia e o bloco simplesmente não é renderizado. Nenhum erro. Nenhuma alteração manual nos templates.

### 3.3 Imports lazy com guard

Quando um app precisa consultar dados de outro em tempo de execução (não na carga do módulo), o import deve ser feito dentro da função com um guard:

```python
def minha_funcao():
    from django.apps import apps
    if not apps.is_installed('outro_app'):
        return
    from outro_app.models import MeuModel
    ...
```

---

## 4. Escopo

### Dentro do escopo

- Algoritmo de recomendação baseado em categoria e autor do histórico do usuário
- Fallback para usuários sem histórico (livros mais populares da biblioteca)
- Exibição na página de detalhe do livro (seção "Você também pode gostar")
- Exibição na home para usuários autenticados (widget "Recomendados para você")
- Carregamento via HTMX (lazy load, sem impacto na performance da página principal)
- Indicação visual de disponibilidade (badge verde/cinza no card)

### Fora do escopo

- Machine learning, embeddings ou modelos estatísticos avançados
- Filtragem colaborativa entre usuários ("usuários parecidos com você também leram")
- Sistema de avaliações ou notas de livros
- Recomendações por e-mail ou notificação push
- Persistência de recomendações no banco (são calculadas sob demanda)
- Recomendações para usuários não autenticados

---

## 5. Algoritmo de Recomendação

### 5.1 Visão geral

O algoritmo é um sistema de pontuação simples e determinístico. Para cada candidato a recomendação, calcula-se um `score` composto, e os livros são ordenados do maior para o menor score antes de retornar ao template.

```
score(livro) = pontos_categoria + pontos_autor + pontos_popularidade
```

### 5.2 Passo a passo

**Passo 1 — Extrair perfil do usuário**

A partir de todos os `Emprestimo` do usuário (status `ativo`, `devolvido` ou `atrasado`), construir dois contadores:

```python
emprestimos = Emprestimo.objects.filter(
    usuario=usuario,
    status__in=['ativo', 'devolvido', 'atrasado']
).select_related('exemplar__livro')

categorias = Counter(e.exemplar.livro.categoria for e in emprestimos)
autores    = Counter(e.exemplar.livro.autor     for e in emprestimos)
```

**Passo 2 — Identificar livros já lidos**

```python
livros_lidos_ids = {e.exemplar.livro_id for e in emprestimos}
if excluir_livro_id:
    livros_lidos_ids.add(excluir_livro_id)
```

**Passo 3 — Selecionar candidatos**

```python
candidatos = Livro.objects.filter(
    biblioteca=usuario.biblioteca
).exclude(id__in=livros_lidos_ids).prefetch_related('exemplares')
```

Para `admin_system` (sem biblioteca fixa): buscar em todas as bibliotecas.

**Passo 4 — Calcular score de cada candidato**

| Critério | Pontos |
|---|---|
| Categoria corresponde à mais frequente do usuário | +4 |
| Categoria corresponde à 2ª mais frequente | +3 |
| Categoria corresponde à 3ª mais frequente | +2 |
| Qualquer outra categoria do histórico | +1 |
| Autor corresponde ao mais lido | +5 |
| Autor corresponde ao 2º mais lido | +4 |
| Qualquer outro autor do histórico | +2 |
| Popularidade geral normalizada (0–3 pts) | +0 a +3 |

Popularidade: `min(total_emprestimos_do_livro, 10) / 10 * 3`

**Passo 5 — Ordenar e limitar**

Ordenar por score decrescente. Retornar no máximo **6 livros**.

**Passo 6 — Cold start (usuário sem histórico)**

Retornar os **6 livros mais emprestados** da biblioteca nos últimos 90 dias:

```python
noventa_dias = timezone.now().date() - timedelta(days=90)
Livro.objects.filter(
    exemplares__historico_emprestimos__data_emprestimo__gte=noventa_dias
).annotate(
    total=Count('exemplares__historico_emprestimos')
).order_by('-total')[:6]
```

---

## 6. Estrutura de Arquivos

```
apps/
└── app_recomendacoes/
    ├── __init__.py
    ├── apps.py
    ├── services.py   ← algoritmo puro (sem imports de outros apps no nível de módulo)
    ├── views.py      ← endpoints HTMX
    └── urls.py       ← rotas

templates/
└── recomendacoes/
    └── partials/
        ├── _lista.html   ← container com título e grid
        └── _card.html    ← card individual de cada livro recomendado
```

Nenhum `models.py` é necessário — as recomendações são computadas em tempo real.

---

## 7. API Interna (Views e URLs)

### 7.1 Endpoint de recomendações para detalhe do livro

```
GET /recomendacoes/livro/<uuid:livro_id>/
```

- Requer autenticação (`@login_required`)
- Retorna o partial `recomendacoes/partials/_lista.html`
- Recebe o `livro_id` atual para excluí-lo dos candidatos

### 7.2 Endpoint de recomendações para a home

```
GET /recomendacoes/para-voce/
```

- Requer autenticação
- Retorna o partial `recomendacoes/partials/_lista.html` sem excluir nenhum livro

---

## 8. Integração na Plataforma (Padrão B — URL lookup condicional)

A integração nos templates segue o **Padrão B** definido na seção 3: a URL é resolvida de forma silenciosa com `{% url ... as var %}`. Se `app_recomendacoes` for removida do projeto, as páginas continuam funcionando normalmente — o bloco simplesmente não é renderizado.

### 8.1 Página de detalhe do livro (`detalhe_livro.html`)

Adicionar ao final do bloco de exemplares, antes de `{% endblock %}`:

```html
{% url 'recomendacoes_livro' livro.pk as url_recomendacoes %}
{% if user.is_authenticated and url_recomendacoes %}
<div class="mt-5"
     hx-get="{{ url_recomendacoes }}"
     hx-trigger="load"
     hx-swap="innerHTML">
    <div class="text-center text-muted py-3">
        <div class="spinner-border spinner-border-sm"></div>
        Carregando recomendações...
    </div>
</div>
{% endif %}
```

O carregamento lazy (`hx-trigger="load"`) garante que a página abre instantaneamente e o bloco de recomendações aparece em seguida sem bloquear a renderização.

### 8.2 Página inicial (`home.html`)

```html
{% url 'recomendacoes_para_voce' as url_recomendacoes_home %}
{% if user.is_authenticated and url_recomendacoes_home %}
<section class="mt-5"
         hx-get="{{ url_recomendacoes_home }}"
         hx-trigger="load"
         hx-swap="innerHTML">
</section>
{% endif %}
```

### 8.3 Fluxo visual do card de recomendação

Cada livro recomendado será exibido em um card compacto com:

- Ícone de livro (Bootstrap Icons `bi-book`)
- Título e autor
- Badge de categoria
- Badge de disponibilidade: `Disponível` (verde) ou `Indisponível` (cinza)
- Link direto para `detalhe_livro`

Layout em grid responsivo: **3 colunas no desktop**, 2 no tablet, 1 no mobile (`col-md-4 col-sm-6 col-12`).

---

## 9. Detalhamento Técnico de Implementação

### 9.1 `services.py` — imports seguros

`services.py` importa de `app_emprestimos` e `app_acervo` **dentro das funções**, com guard de `apps.is_installed`, seguindo o Padrão A descrito na seção 3.3:

```python
from collections import Counter
from datetime import timedelta
from django.utils import timezone

def gerar_recomendacoes(usuario, excluir_livro_id=None, limite=6):
    from django.apps import apps
    if not apps.is_installed('app_emprestimos') or not apps.is_installed('app_acervo'):
        return []

    from app_emprestimos.models import Emprestimo
    from app_acervo.models import Livro

    emprestimos = Emprestimo.objects.filter(
        usuario=usuario,
        status__in=['ativo', 'devolvido', 'atrasado']
    ).select_related('exemplar__livro')

    if not emprestimos.exists():
        return _livros_populares(usuario, excluir_livro_id, limite)

    livros_lidos_ids = {e.exemplar.livro_id for e in emprestimos}
    if excluir_livro_id:
        livros_lidos_ids.add(excluir_livro_id)

    categorias = Counter(e.exemplar.livro.categoria for e in emprestimos)
    autores    = Counter(e.exemplar.livro.autor     for e in emprestimos)

    candidatos = Livro.objects.filter(
        biblioteca=usuario.biblioteca
    ).exclude(id__in=livros_lidos_ids).prefetch_related('exemplares')

    scored = sorted(
        ((  _calcular_score(livro, categorias, autores), livro) for livro in candidatos),
        key=lambda x: x[0],
        reverse=True,
    )
    return [livro for _, livro in scored[:limite]]
```

### 9.2 `apps.py`

```python
from django.apps import AppConfig

class AppRecomendacoesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_recomendacoes'
```

Não há sinais para conectar — `app_recomendacoes` apenas consulta dados, não reage a eventos.

### 9.3 `views.py`

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .services import gerar_recomendacoes

@login_required
def recomendacoes_livro(request, livro_id):
    livros = gerar_recomendacoes(request.user, excluir_livro_id=livro_id)
    return render(request, 'recomendacoes/partials/_lista.html', {
        'livros': livros,
        'titulo': 'Você também pode gostar',
    })

@login_required
def recomendacoes_para_voce(request):
    livros = gerar_recomendacoes(request.user)
    return render(request, 'recomendacoes/partials/_lista.html', {
        'livros': livros,
        'titulo': 'Recomendados para você',
    })
```

### 9.4 `urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('livro/<uuid:livro_id>/', views.recomendacoes_livro,    name='recomendacoes_livro'),
    path('para-voce/',             views.recomendacoes_para_voce, name='recomendacoes_para_voce'),
]
```

Registrar em `config/urls.py`:
```python
path('recomendacoes/', include('app_recomendacoes.urls')),
```

E em `config/settings.py`:
```python
INSTALLED_APPS = [
    ...
    'app_recomendacoes',
]
```

---

## 10. Casos de Uso e Comportamentos Esperados

| Situação | Comportamento |
|---|---|
| Usuário com histórico rico (5+ livros) | Recomendações fortemente personalizadas por categoria e autor |
| Usuário com pouco histórico (1–4 livros) | Mix de personalização + popularidade global |
| Usuário sem nenhum empréstimo | 6 livros mais populares dos últimos 90 dias |
| Todos os candidatos já foram lidos | Retorna lista vazia; seção não é renderizada |
| Livro recomendado sem exemplar disponível | Exibido com badge "Indisponível" |
| Usuário não autenticado | Seção não aparece; endpoints retornam redirect para login |
| `app_recomendacoes` removida do projeto | Templates não renderizam a seção (URL lookup retorna vazio) |
| `app_emprestimos` removida do projeto | `services.py` retorna `[]` via guard; nenhum erro |

---

## 11. Critérios de Aceite

- [ ] A seção "Você também pode gostar" aparece na página de detalhe do livro para usuários autenticados
- [ ] A seção "Recomendados para você" aparece na home para usuários autenticados
- [ ] Ambas as seções são carregadas via HTMX sem bloquear a página
- [ ] Livros já emprestados pelo usuário não aparecem nas recomendações
- [ ] O livro atual (no detalhe) não aparece na lista de recomendações
- [ ] Usuários sem histórico veem os livros mais populares
- [ ] Cards exibem título, autor, categoria e badge de disponibilidade
- [ ] Card é clicável e leva ao detalhe do livro
- [ ] Seções não aparecem para usuários não autenticados
- [ ] Remover `app_recomendacoes` de `INSTALLED_APPS` não quebra nenhuma outra página
- [ ] Nenhuma query N+1 é introduzida (`select_related` e `prefetch_related` em uso)

---

## 12. Dependências e Riscos

| Item | Detalhe |
|---|---|
| **Sem dependências externas** | Tudo baseado em Django ORM e dados existentes |
| **Modularidade garantida** | Imports lazy com guard; integração via URL lookup condicional nos templates |
| **Performance** | Recomendações calculadas a cada requisição. Aceitável com SQLite e volume acadêmico. Se o acervo crescer, considerar `django.core.cache` |
| **Qualidade das recomendações** | Depende do volume de histórico. Coberto pelo fallback de popularidade para usuários novos |
| **Campo `categoria`** | É um `CharField` livre. Inconsistências de nomenclatura reduzem a precisão. Normalizar esse campo está fora do escopo desta fase |

---

## 13. Resumo das Alterações no Projeto

| Arquivo | Ação |
|---|---|
| `apps/app_recomendacoes/__init__.py` | Criar (vazio) |
| `apps/app_recomendacoes/apps.py` | Criar |
| `apps/app_recomendacoes/services.py` | Criar — algoritmo com imports lazy guardados |
| `apps/app_recomendacoes/views.py` | Criar — 2 endpoints HTMX |
| `apps/app_recomendacoes/urls.py` | Criar — 2 rotas |
| `config/settings.py` | Adicionar `app_recomendacoes` em `INSTALLED_APPS` |
| `config/urls.py` | Registrar `/recomendacoes/` |
| `templates/recomendacoes/partials/_lista.html` | Criar — container da seção |
| `templates/recomendacoes/partials/_card.html` | Criar — card individual |
| `templates/acervo/detalhe_livro.html` | Adicionar bloco `{% url ... as var %}` antes de `{% endblock %}` |
| `templates/home.html` | Adicionar bloco `{% url ... as var %}` para usuários autenticados |

**Total: 11 arquivos. Nenhuma migração de banco de dados necessária.**
