from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
import json

from apps.usuarios.models import Perfil, Equipe, Carteira
from apps.core.choices import PerfilAgente, EscopoAgente


# ═══════════════════════════════════════════
# PERFIS
# ═══════════════════════════════════════════

@login_required
@require_GET
def lista_configuracoes(request):
    """Tela principal de configurações: Perfis e Equipes."""
    empresa = request.empresa

    perfis = (
        Perfil.objects
        .filter(empresa=empresa)
        .select_related('grupo')
        .order_by('codigo')
    )
    equipes = (
        Equipe.objects
        .filter(empresa=empresa)
        .select_related('responsavel')
        .order_by('nome')
    )
    usuarios = (
        User.objects
        .filter(agente__carteira__empresa=empresa, is_active=True)
        .order_by('first_name')
    )
    groups = Group.objects.all().order_by('name')

    context = {
        'perfis': perfis,
        'equipes': equipes,
        'usuarios': usuarios,
        'groups': groups,
        'perfil_choices': PerfilAgente.choices,
        'escopo_choices': EscopoAgente.choices,
    }
    return render(request, 'configuracoes/configuracoes.html', context)


@login_required
def perfil_detail(request, perfil_id=None):
    """GET → dados para preencher drawer | POST → criar ou editar."""
    empresa = request.empresa

    if request.method == 'GET':
        if perfil_id:
            perfil = get_object_or_404(Perfil, pk=perfil_id, empresa=empresa)
            data = {
                'id': perfil.id,
                'codigo': perfil.codigo,
                'escopo': perfil.escopo,
                'grupo_id': perfil.grupo_id,
                'ativo': perfil.ativo,
            }
        else:
            data = {}

        return JsonResponse({
            'perfil': data,
            'perfil_choices': PerfilAgente.choices,
            'escopo_choices': EscopoAgente.choices,
            'groups': list(Group.objects.values('id', 'name').order_by('name')),
        })

    # POST — criar ou editar
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'messages': {'perfil': {'__all__': ['JSON inválido']}}},
            status=400
        )

    codigo   = data.get('codigo', '').strip()
    escopo   = data.get('escopo', '').strip()
    grupo_id = data.get('grupo_id')
    ativo    = data.get('ativo', True)
    criar_grupo_nome = data.get('criar_grupo_nome', '').strip()

    errors = {}
    if not codigo:
        errors['codigo'] = ['Código do perfil é obrigatório.']
    if not escopo:
        errors['escopo'] = ['Escopo é obrigatório.']

    if errors:
        return JsonResponse(
            {'success': False, 'messages': {'perfil': errors}}, status=400
        )

    try:
        with transaction.atomic():
            # Resolve o grupo: cria novo ou usa existente
            grupo = None
            if criar_grupo_nome:
                grupo, _ = Group.objects.get_or_create(name=criar_grupo_nome)
            elif grupo_id:
                grupo = get_object_or_404(Group, pk=grupo_id)

            if perfil_id:
                perfil = get_object_or_404(Perfil, pk=perfil_id, empresa=empresa)
                perfil.codigo = codigo
                perfil.escopo = escopo
                perfil.grupo  = grupo
                perfil.ativo  = ativo
                perfil.save()
                msg = 'Perfil atualizado com sucesso!'
            else:
                perfil = Perfil.objects.create(
                    empresa=empresa,
                    codigo=codigo,
                    escopo=escopo,
                    grupo=grupo,
                    ativo=ativo,
                )
                msg = 'Perfil criado com sucesso!'

        return JsonResponse({
            'success': True,
            'messages': {'perfil': {'success': [msg]}}
        })

    except Exception as e:
        return JsonResponse(
            {'success': False, 'messages': {'perfil': {'__all__': [str(e)]}}},
            status=400
        )


@login_required
@require_POST
def perfil_toggle(request, perfil_id):
    """Ativa / desativa um perfil."""
    perfil = get_object_or_404(Perfil, pk=perfil_id, empresa=request.empresa)
    perfil.ativo = not perfil.ativo
    perfil.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': perfil.ativo,
        'messages': {'perfil': {'success': [
            f'Perfil {"ativado" if perfil.ativo else "desativado"} com sucesso!'
        ]}}
    })


# ═══════════════════════════════════════════
# EQUIPES
# ═══════════════════════════════════════════

@login_required
def equipe_detail(request, equipe_id=None):
    """GET → dados para drawer | POST → criar ou editar."""
    empresa = request.empresa

    if request.method == 'GET':
        usuarios = list(
            User.objects
            .filter(agente__carteira__empresa=empresa, is_active=True)
            .values('id', 'first_name', 'last_name', 'username')
            .order_by('first_name')
        )

        if equipe_id:
            equipe = get_object_or_404(Equipe, pk=equipe_id, empresa=empresa)
            data = {
                'id': equipe.id,
                'nome': equipe.nome,
                'responsavel_id': equipe.responsavel_id,
                'ativo': equipe.ativo,
            }
        else:
            data = {}

        return JsonResponse({'equipe': data, 'usuarios': usuarios})

    # POST
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'messages': {'equipe': {'__all__': ['JSON inválido']}}},
            status=400
        )

    nome           = data.get('nome', '').strip()
    responsavel_id = data.get('responsavel_id') or None
    ativo          = data.get('ativo', True)

    if not nome:
        return JsonResponse(
            {'success': False, 'messages': {'equipe': {'nome': ['Nome é obrigatório.']}}},
            status=400
        )

    responsavel = None
    if responsavel_id:
        responsavel = get_object_or_404(
            User, pk=responsavel_id, agente__carteira__empresa=empresa
        )

    try:
        with transaction.atomic():
            if equipe_id:
                equipe = get_object_or_404(Equipe, pk=equipe_id, empresa=empresa)
                equipe.nome        = nome
                equipe.responsavel = responsavel
                equipe.ativo       = ativo
                equipe.save()
                msg = 'Equipe atualizada com sucesso!'
            else:
                equipe = Equipe.objects.create(
                    empresa=empresa,
                    nome=nome,
                    responsavel=responsavel,
                    ativo=ativo,
                )
                msg = 'Equipe criada com sucesso!'

        return JsonResponse({
            'success': True,
            'messages': {'equipe': {'success': [msg]}}
        })

    except Exception as e:
        return JsonResponse(
            {'success': False, 'messages': {'equipe': {'__all__': [str(e)]}}},
            status=400
        )


@login_required
@require_POST
def equipe_toggle(request, equipe_id):
    """Ativa / desativa uma equipe."""
    equipe = get_object_or_404(Equipe, pk=equipe_id, empresa=request.empresa)
    equipe.ativo = not equipe.ativo
    equipe.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': equipe.ativo,
        'messages': {'equipe': {'success': [
            f'Equipe {"ativada" if equipe.ativo else "desativada"} com sucesso!'
        ]}}
    })