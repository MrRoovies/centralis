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
        'equipe_id',
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
        'perfis': Perfil.objects.filter(ativo=True, empresa=empresa).order_by('codigo'),
        'equipes': Equipe.objects.filter(ativo=True, empresa=empresa).order_by('nome'),
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

        registrar = AgenteService.registra_usuario(data, empresa)
        if not registrar['success']:
            return JsonResponse(registrar, status=400)

        return JsonResponse(registrar, status=201)

    # GET → retorna dados para o modal de criação
    context = {
        'carteiras': list(Carteira.objects.filter(empresa=empresa, ativo=True).values('id', 'nome')),
        'equipes': list(Equipe.objects.filter(ativo=True, empresa=empresa).values('id', 'nome')),
        'perfis': list(Perfil.objects.filter(ativo=True, empresa=empresa).values('id', 'codigo')),
    }
    return JsonResponse(context)

@login_required
@require_POST
def toggle_ativo_agente(request, agente_id):
    """Ativa ou desativa um agente."""
    agente = get_object_or_404(
        Agente.objects.select_related('usuario', 'perfil'),
        pk=agente_id,
        perfil__empresa=request.empresa
    )

    if agente.usuario_id == request.user.id:
        return JsonResponse(
            {
            'success': False,
            'messages': {'agente': ['Você não pode desativar seu próprio usuário.']}
        }, status=403)

    agente.usuario.is_active = not agente.usuario.is_active
    agente.usuario.save(update_fields=['is_active'])
    status = 'ativado' if agente.usuario.is_active else 'desativado'
    return JsonResponse({
        'success': True,
        'is_active': agente.usuario.is_active,
        'messages': {'agente': {'success': [f'Agente {status} com sucesso!']}}
    })


@login_required
def editar_agente(request, agente_id):
    """Retorna dados do agente (GET) e salva edição (POST)."""
    empresa = request.empresa
    agente = get_object_or_404(
        Agente.objects.select_related('usuario', 'perfil', 'equipe', 'carteira'),
        pk=agente_id,
        perfil__empresa=empresa
    )
    equipe_id = agente.equipe.id if agente.equipe else None

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'messages': {'agente': {'__all__': ['JSON inválido']}}}, status=400)

        edita_usuario = AgenteService.edita_usuario(data, agente, empresa)
        if not edita_usuario['success']:
            return JsonResponse(edita_usuario, status=400)

        return JsonResponse(edita_usuario, status=200)

    context = {
        'agente': {
            'id': agente.id,
            'first_name': agente.usuario.first_name,
            'last_name': agente.usuario.last_name,
            'email': agente.email or '',
            'cpf': agente.cpf or '',
            'perfil_id': agente.perfil.id,
            'equipe_id': equipe_id,
        },
        'perfis': list(Perfil.objects.filter(ativo=True, empresa=empresa).values('id', 'codigo')),
        'equipes': list(Equipe.objects.filter(ativo=True, empresa=empresa).values('id', 'nome')),
    }
    return JsonResponse(context)


