from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from apps.usuarios.models import Agente, Carteira, Perfil, Equipe
from django.views.decorators.http import require_GET, require_POST

from apps.usuarios.services.agente_service import AgenteService

import json

@login_required
@require_GET
def lista_agentes(request):
    """Lista todos os agentes da empresa com filtros."""
    empresa = request.empresa
    usuario = request.user
    agentes = AgenteService.get_agentes(empresa)
    params = request.GET.copy()
    params.pop('page', None)

    campos_permitidos = [
        'carteira_id',
        'perfil_id',
        'usuario__is_active',
    ]
    filtro = {
        k: v
        for k, v in params.dict().items()
        if k in campos_permitidos and v != ''
    }

    queryset = AgenteService.filtrar(agentes, filtro, usuario)

    total = queryset.count()
    ativos = queryset.filter(usuario__is_active=True).count()

    paginator = Paginator(queryset, 20)
    page = request.GET.get('page')
    agentes_page = paginator.get_page(page)

    context = {
        'agentes': agentes_page,
        'carteiras': Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
        'perfis': Perfil.objects.filter(ativo=True).order_by('codigo'),
        'filtros': filtro,
        'total': total,
        'ativos': ativos,
        'inativos': total - ativos,
        'query_string': params.urlencode(),
    }
    return render(request, 'agentes/agentes_list.html', context)


@login_required
def novo_agente(request):
    """Cria um novo agente (User + Agente)."""
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'messages': {'__all__': ['JSON inválido']}}, status=400)

        campos_obrigatorios = AgenteService.campos_obrigatorios(data, empresa)

        if not campos_obrigatorios['success']:
            return JsonResponse(campos_obrigatorios, status=400)

        return JsonResponse(campos_obrigatorios, status=201)

    # GET → retorna dados para o modal de criação
    context = {
        'carteiras': list(Carteira.objects.filter(empresa=empresa, ativo=True).values('id', 'nome')),
        'equipes': list(Equipe.objects.filter(ativo=True).values('id', 'nome')),
        'perfis': list(Perfil.objects.filter(ativo=True).values('id', 'codigo')),
    }
    return JsonResponse(context)

@login_required
@require_POST
def toggle_ativo_agente(request, agente_id):
    """Ativa ou desativa um agente."""
    agente = get_object_or_404(
        Agente,
        pk=agente_id,
        carteira__empresa=request.empresa
    )
    agente.usuario.is_active = not agente.usuario.is_active
    agente.usuario.save(update_fields=['is_active'])
    status = 'ativado' if agente.usuario.is_active else 'desativado'
    return JsonResponse({
        'success': True,
        'is_active': agente.usuario.is_active,
        'messages': {'agente': {'success': [f'Agente {status} com sucesso!']}}
    })