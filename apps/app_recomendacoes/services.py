from collections import Counter
from datetime import timedelta
from django.utils import timezone


def gerar_recomendacoes(usuario, excluir_livro_id=None, limite=6):
    from django.apps import apps
    if not apps.is_installed('app_emprestimos') or not apps.is_installed('app_acervo'):
        return []

    from django.db.models import Count, Exists, OuterRef
    from app_emprestimos.models import Emprestimo
    from app_acervo.models import Exemplar

    emprestimos = list(
        Emprestimo.objects.filter(
            usuario=usuario,
            status__in=['ativo', 'devolvido', 'atrasado'],
        ).select_related('exemplar__livro')
    )

    # IDs a excluir em todos os níveis: livros já lidos + livro atual da página
    excluir_ids = {e.exemplar.livro_id for e in emprestimos}
    if excluir_livro_id:
        excluir_ids.add(excluir_livro_id)

    resultado = []

    # Nível 1 — personalizado por score (só se há histórico)
    if emprestimos:
        categorias = Counter(e.exemplar.livro.categoria for e in emprestimos)
        autores    = Counter(e.exemplar.livro.autor     for e in emprestimos)

        candidatos = list(
            _queryset_base(usuario)
            .exclude(id__in=excluir_ids)
            .annotate(
                has_disponivel=Exists(
                    Exemplar.objects.filter(livro=OuterRef('pk'), status='disponivel')
                ),
                total_emprestimos=Count('exemplares__historico_emprestimos', distinct=True),
            )
        )
        scored = sorted(
            ((_calcular_score(livro, categorias, autores), livro) for livro in candidatos),
            key=lambda x: x[0],
            reverse=True,
        )
        resultado = [livro for _, livro in scored[:limite]]

    # Nível 2 — completa com mais populares dos últimos 90 dias
    if len(resultado) < limite:
        ja_vistos = excluir_ids | {livro.id for livro in resultado}
        resultado += _populares_recentes(usuario, ja_vistos, limite - len(resultado))

    # Nível 3 — completa com quaisquer livros do acervo (nunca fica abaixo de 6)
    if len(resultado) < limite:
        ja_vistos = excluir_ids | {livro.id for livro in resultado}
        resultado += _quaisquer_livros(usuario, ja_vistos, limite - len(resultado))

    return resultado


def _populares_recentes(usuario, excluir_ids, limite):
    from django.db.models import Count, Exists, OuterRef
    from app_acervo.models import Exemplar

    noventa_dias = timezone.now().date() - timedelta(days=90)

    return list(
        _queryset_base(usuario)
        .exclude(id__in=excluir_ids)
        .filter(exemplares__historico_emprestimos__data_emprestimo__gte=noventa_dias)
        .annotate(
            has_disponivel=Exists(
                Exemplar.objects.filter(livro=OuterRef('pk'), status='disponivel')
            ),
            total=Count('exemplares__historico_emprestimos', distinct=True),
        )
        .order_by('-total')[:limite]
    )


def _quaisquer_livros(usuario, excluir_ids, limite):
    from django.db.models import Count, Exists, OuterRef
    from app_acervo.models import Exemplar

    return list(
        _queryset_base(usuario)
        .exclude(id__in=excluir_ids)
        .annotate(
            has_disponivel=Exists(
                Exemplar.objects.filter(livro=OuterRef('pk'), status='disponivel')
            ),
            total=Count('exemplares__historico_emprestimos', distinct=True),
        )
        .order_by('-total', 'titulo')[:limite]
    )


def _queryset_base(usuario):
    from app_acervo.models import Livro
    if getattr(usuario, 'is_admin_system', False) or usuario.biblioteca is None:
        return Livro.objects.all()
    return Livro.objects.filter(biblioteca=usuario.biblioteca)


def _calcular_score(livro, categorias, autores):
    score = 0.0
    cats = [c for c, _ in categorias.most_common()]
    auts = [a for a, _ in autores.most_common()]

    if livro.categoria in cats:
        idx = cats.index(livro.categoria)
        score += max(4 - idx, 1)

    if livro.autor in auts:
        idx = auts.index(livro.autor)
        score += max(5 - idx, 2)

    total = getattr(livro, 'total_emprestimos', 0) or 0
    score += min(total, 10) / 10 * 3

    return score
