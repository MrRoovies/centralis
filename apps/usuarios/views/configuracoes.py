from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
import json

from apps.usuarios.models import Perfil, Equipe, Carteira
from apps.core.choices import PerfilAgente, EscopoAgente
from apps.usuarios.services.equipe_perfil_service import PerfilService

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
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'messages': {'perfil': {'__all__': ['JSON inválido']}}},
                status=400
            )

        campos_obrigatorios = PerfilService.campos_obrigatorios(data)
        if not campos_obrigatorios['success']:
            return JsonResponse(campos_obrigatorios, status=400)

        cria_ou_edita = PerfilService.cria_ou_edita(data, perfil_id, empresa)
        if not cria_ou_edita['success']:
            return JsonResponse(cria_ou_edita, status=400)

        return JsonResponse(cria_ou_edita, status=200)


    """GET → dados para preencher drawer | POST → criar ou editar."""
    return JsonResponse({
        'perfil': PerfilService.detalhes(perfil_id, empresa),
        'perfil_choices': PerfilAgente.choices,
        'escopo_choices': EscopoAgente.choices,
        'groups': list(Group.objects.values('id', 'name').order_by('name')),
    })


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