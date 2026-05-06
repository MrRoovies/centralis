from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

from apps.agenda.models import Situacao  # ajuste o import conforme seu app
from apps.core.choices import TipoSituacao


# ─── Página principal ────────────────────────────────────────
@login_required
def situacoes_view(request):
    situacoes = Situacao.objects.all().order_by('nome')

    context = {
        'situacoes':      situacoes,
        'total_ativas':   situacoes.filter(ativo=True).count(),
        'total_inativas': situacoes.filter(ativo=False).count(),
    }
    return render(request, 'configuracoes/situacoes.html', context)


# ─── Criar / Editar ──────────────────────────────────────────
@login_required
@require_http_methods(['GET', 'POST'])
def situacao_detail(request, situacao_id=None):

    # ── GET: carrega dados para o drawer ──────────────────────
    if request.method == 'GET':
        if situacao_id:
            try:
                s = Situacao.objects.get(pk=situacao_id)
                data = {
                    'situacao': {
                        'id': s.id,
                        'nome': s.nome,
                        'ativo': s.ativo,
                        'tipo': s.tipo,
                    },'tipos': TipoSituacao.choices
                }
            except Situacao.DoesNotExist:
                return JsonResponse(
                    {'messages': {'situacao': {'__all__': ['Situação não encontrada.']}}},
                    status=404
                )
        else:
            # Novo: retorna objeto vazio para o drawer abrir limpo
            data = {'situacao': {}, 'tipos': TipoSituacao.choices}

        return JsonResponse(data)

    # ── POST: salva (criação ou edição) ───────────────────────
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {'messages': {'situacao': {'__all__': ['Dados inválidos.']}}},
            status=400
        )

    nome      = payload.get('nome', '').strip()
    tipo      = payload.get('tipo')
    ativo     = payload.get('ativo', True)

    # Validações
    errors = {}

    if not nome:
        errors['nome'] = ['O nome é obrigatório.']

    if errors:
        return JsonResponse({'messages': {'situacao': errors}}, status=400)

    # Persistência
    if situacao_id:
        try:
            situacao = Situacao.objects.get(pk=situacao_id)
        except Situacao.DoesNotExist:
            return JsonResponse(
                {'messages': {'situacao': {'__all__': ['Situação não encontrada.']}}},
                status=404
            )
        situacao.nome = nome
        situacao.ativo = ativo
        situacao.tipo = tipo
        situacao.save()
        msg = 'Situação atualizada com sucesso!'
    else:
        situacao = Situacao.objects.create(
            nome=nome,
            tipo=tipo,
                # descricao=descricao,
                # cor=cor,
            ativo=ativo,
        )
        msg = 'Situação criada com sucesso!'

    return JsonResponse({
        'messages': {'situacao': {'success': [msg]}},
        'id': situacao.id,
    })


# ─── Toggle ativo / inativo ───────────────────────────────────
@login_required
@require_http_methods(['POST'])
def situacao_toggle(request, situacao_id):
    try:
        situacao = Situacao.objects.get(pk=situacao_id)
    except Situacao.DoesNotExist:
        return JsonResponse(
            {'messages': {'situacao': {'__all__': ['Situação não encontrada.']}}},
            status=404
        )

    situacao.ativo = not situacao.ativo
    situacao.save(update_fields=['ativo'])

    return JsonResponse({'ativo': situacao.ativo})


# ─── Helper ───────────────────────────────────────────────────
def _cor_valida(cor):
    """Valida formato hexadecimal #RRGGBB ou #RGB."""
    import re
    return bool(re.match(r'^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$', cor))