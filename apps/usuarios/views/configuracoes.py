from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from apps.core.decorators import role_required
import json

from apps.usuarios.models import Perfil, Equipe, Carteira, Agente
from apps.core.choices import PerfilAgente, EscopoAgente
from apps.usuarios.services.equipe_perfil_service import (
    EquipeService, PerfilService, campos_obrigatorios, CarteiraService)

# ═══════════════════════════════════════════
# PERFIS
# ═══════════════════════════════════════════

@login_required
@require_GET
def lista_configuracoes(request):
    """Tela principal de configurações: Perfis e Equipes."""
    empresa = request.empresa

    carteiras = (
        Carteira.objects
        .filter(empresa=empresa)
        .order_by('nome')
    )

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
        'carteiras': carteiras,
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

        campos = ['codigo', 'escopo', 'grupo_id']
        validacao = campos_obrigatorios(data, 'perfil', campos)
        if not validacao.get('success'):
            return JsonResponse(validacao, status=400)

        cria_ou_edita = PerfilService.cria_ou_edita(data, perfil_id, empresa)
        if not cria_ou_edita.get('success'):
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

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'messages': {'equipe': {'__all__': ['JSON inválido']}}},
                status=400
            )

        campos = ['nome', 'ativo']
        validacao = campos_obrigatorios(data, 'equipe', campos)
        if not validacao.get('success'):
            return JsonResponse(validacao, status=400)

        cria_ou_edita = EquipeService.cria_ou_edita(data, equipe_id, empresa)
        if not cria_ou_edita.get('success'):
            return JsonResponse(cria_ou_edita, status=400)

        return JsonResponse(cria_ou_edita, status=200)


    # Detalhes de equipe - GET:
    detalhes = EquipeService.detalhes(equipe_id, empresa)
    if not detalhes.get('success'):
        return JsonResponse(detalhes, status=400)

    return JsonResponse(detalhes['data'], status=200)



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


@login_required
def carteira_detail(request, carteira_id=None):
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'messages': {'carteira': {'__all__': ['JSON inválido']}}},
                status=400
            )
        print(data)
        campos = ['nome', 'ativo']
        validacao = campos_obrigatorios(data, 'carteira', campos)
        if not validacao.get('success'):
            return JsonResponse(validacao, status=400)

        cria_ou_edita = CarteiraService.cria_ou_edita(data, carteira_id, empresa)
        if not cria_ou_edita.get('success'):
            return JsonResponse(cria_ou_edita, status=400)

        return JsonResponse(cria_ou_edita, status=200)

    # --- GET ---
    detalhes = CarteiraService.detalhes(carteira_id, empresa)
    if not detalhes.get('success'):
        return JsonResponse(detalhes['data'], status=400)

    return JsonResponse(detalhes['data'], status=200)


@login_required
@require_POST
def carteira_toggle(request, carteira_id):
    """Ativa / desativa uma equipe."""
    carteira = get_object_or_404(Carteira, pk=carteira_id, empresa=request.empresa)
    carteira.ativo = not carteira.ativo
    carteira.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': carteira.ativo,
        'messages': {'equipe': {'success': [
            f'Equipe {"ativada" if carteira.ativo else "desativada"} com sucesso!'
        ]}}
    })