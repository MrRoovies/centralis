# views/view_permissions.py
# Cole este conteúdo na sua views.py ou num arquivo dedicado.

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from apps.core.models import ViewPermission
from collections import defaultdict


# ── Choices que espelham os códigos de perfil do sistema ──────
ROLE_CHOICES = [
    ('ADM',        'Administrador'),
    ('DIRETOR',    'Diretor'),
    ('GERENTE',    'Gerente'),
    ('SUPERVISOR', 'Supervisor'),
    ('AGENTE',     'Agente'),
    ('VISITANTE',  'Visitante'),
]


def _success(msg, extra=None):
    data = {'messages': {'permissao': {'success': [msg]}}}
    if extra:
        data.update(extra)
    return data


def _error(campo, msg, status=400):
    return JsonResponse(
        {'messages': {'permissao': {campo: [msg]}}},
        status=status,
    )


# ════════════════════════════════════════════════════════════
# LISTAGEM
# ════════════════════════════════════════════════════════════

@login_required
def view_permissions_list(request):
    """Tela principal — listagem de ViewPermission."""
    permissoes = ViewPermission.objects.exclude(app_name=None).order_by('app_name')

    apps = defaultdict(list)
    for p in permissoes:
        apps[p.app_name].append(p)

    total_publico = permissoes.filter(roles=[]).count()
    total_restrito = permissoes.exclude(roles=[]).count()

    return render(request, 'configuracoes/view_permissions.html', {
        'permissoes':     permissoes,
        'apps': apps,
        'total_publico':  total_publico,
        'total_restrito': total_restrito,
        'role_choices':   ROLE_CHOICES,
    })


# ════════════════════════════════════════════════════════════
# CRIAR
# ════════════════════════════════════════════════════════════

@login_required
@require_http_methods(['POST'])
def view_permission_nova(request):
    """Cria uma nova ViewPermission via JSON."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return _error('__all__', 'Payload inválido.')

    url_name = payload.get('url_name', '').strip()
    roles    = payload.get('roles', [])

    # ── Validações ────────────────────────────────────────────
    if not url_name:
        return _error('url_name', 'O nome da URL é obrigatório.')

    if ViewPermission.objects.filter(url_name=url_name).exists():
        return _error('url_name', f'Já existe uma regra para "{url_name}".')

    roles_validos = {r for r, _ in ROLE_CHOICES}
    roles_invalidos = [r for r in roles if r not in roles_validos]
    if roles_invalidos:
        return _error('roles', f'Perfis inválidos: {", ".join(roles_invalidos)}')

    # ── Criação ───────────────────────────────────────────────
    perm = ViewPermission.objects.create(url_name=url_name, roles=roles)

    return JsonResponse(
        _success(f'Permissão "{url_name}" criada com sucesso!', {'id': perm.id}),
        status=201,
    )


# ════════════════════════════════════════════════════════════
# EDITAR (GET = carregar, POST = salvar)
# ════════════════════════════════════════════════════════════

@login_required
@require_http_methods(['GET', 'POST'])
def view_permission_editar(request, perm_id):
    try:
        perm = ViewPermission.objects.get(pk=perm_id)
    except ViewPermission.DoesNotExist:
        return JsonResponse({'messages': {'permissao': {'__all__': ['Permissão não encontrada.']}}}, status=404)

    # ── GET: retorna dados para preencher o drawer ─────────────
    if request.method == 'GET':
        return JsonResponse({
            'permissao': {
                'id':       perm.id,
                'url_name': perm.url_name,
                'roles':    perm.roles,
            }
        })

    # ── POST: salva alterações ─────────────────────────────────
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return _error('__all__', 'Payload inválido.')

    url_name = payload.get('url_name', '').strip()
    roles    = payload.get('roles', [])

    if not url_name:
        return _error('url_name', 'O nome da URL é obrigatório.')

    # Verifica duplicidade (excluindo o próprio registro)
    if ViewPermission.objects.filter(url_name=url_name).exclude(pk=perm_id).exists():
        return _error('url_name', f'Já existe outra regra para "{url_name}".')

    roles_validos = {r for r, _ in ROLE_CHOICES}
    roles_invalidos = [r for r in roles if r not in roles_validos]
    if roles_invalidos:
        return _error('roles', f'Perfis inválidos: {", ".join(roles_invalidos)}')

    perm.url_name = url_name
    perm.roles    = roles
    perm.save()

    return JsonResponse(_success(f'Permissão "{url_name}" atualizada com sucesso!'))


# ════════════════════════════════════════════════════════════
# EXCLUIR
# ════════════════════════════════════════════════════════════

@login_required
@require_http_methods(['POST'])
def view_permission_excluir(request, perm_id):
    try:
        perm = ViewPermission.objects.get(pk=perm_id)
    except ViewPermission.DoesNotExist:
        return JsonResponse({'messages': {'permissao': {'__all__': ['Permissão não encontrada.']}}}, status=404)

    url_name = perm.url_name
    perm.delete()

    return JsonResponse(_success(f'Permissão "{url_name}" excluída com sucesso!'))