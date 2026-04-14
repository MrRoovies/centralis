import json
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from ..services.relatorio_vendas import RelatorioVendasService
from apps.vendas.services.vendas_services import VendasService
from django.utils import timezone
from django.core.paginator import Paginator
from apps.agenda.models import Agenda, Acionamento
from apps.vendas.models import Venda, Esteira, HistVenda, Oferta
from django.contrib.auth import get_user_model
from apps.core.responses.pattern import ResponsePattern
from apps.core.helpers.change_tracker import ChangeTracker

User = get_user_model()
@require_GET
@login_required
def detalhe_venda(request, venda_id):
    agente = request.user
    venda = get_object_or_404(
        Venda.objects
        .select_related(
            'cliente', 'oferta__produto', 'oferta__parceiro',
            'esteira', 'usuario', 'agenda'
        )
        .prefetch_related('historico__esteira', 'historico__usuario'),
        pk=venda_id,
        empresa=request.empresa
    )

    historico = venda.historico.order_by('-data')

    esteiras = Esteira.objects.filter(
        empresa=request.empresa,
        carteira=agente.agente.carteira,
        ativo=True
    ).order_by('ordem')

    usuarios = User.objects.filter(
        agente__carteira__empresa=request.empresa
    ).order_by('first_name')

    # comissão calculada: valor * comissao%
    comissao_valor = (venda.valor * venda.comissao / 100).quantize(
        __import__('decimal').Decimal('0.01')
    )

    return render(request, 'relatorios/venda_detalhe.html', {
        'venda': venda,
        'historico': historico,
        'esteiras': esteiras,
        'usuarios': usuarios,
        'comissao_valor': comissao_valor,
    })


@login_required
@require_POST
def editar_valores(request, venda_id):
    venda = get_object_or_404(Venda, pk=venda_id, empresa=request.empresa)
    user = request.user
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        messages = ['JSON inválido']
        return JsonResponse(
            ResponsePattern.error("json", messages, status=400)
        )
    valores_e_formatos = VendasService.valores_e_formatos(data)

    if not valores_e_formatos.get('success'):
        return JsonResponse(valores_e_formatos, status=400)

    changes = ChangeTracker.verifica_alteracoes(venda, data)
    if not changes:
        return JsonResponse(ResponsePattern.error('valores_venda', ["Nenhuma mudanca encontrada"]), status=400)

    update = VendasService.update_valores(venda, valores_e_formatos['data'], user, changes)
    if not update.get('success'):
        return JsonResponse(update, status=400)

    return JsonResponse(update, status=200)


@login_required
@require_POST
def editar_oferta(request, venda_id):
    empresa = request.empresa
    venda = get_object_or_404(Venda, pk=venda_id, empresa=empresa)
    user = request.user

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(ResponsePattern.error('__all__', ['JSON inválido']), status=400)

    oferta_id = data.get('oferta')
    prazo = data.get('prazo')

    oferta = get_object_or_404(
        Oferta.objects.select_related('produto', 'parceiro'), pk=oferta_id, empresa=empresa)

    dados = {'oferta': oferta, 'prazo': prazo}
    alteracoes = ChangeTracker.verifica_alteracoes(venda, dados)
    if not alteracoes and prazo in [None, '']:
        return JsonResponse(
            ResponsePattern.error('esteira', ["Prazo não pode ser vazio.", "Nenhuma mudança encontrada"]),
            status=400)

    atualiza_oferta = VendasService.atualiza_oferta_prazo(venda, user, oferta, prazo, alteracoes)
    if not atualiza_oferta.get('success'):
        return JsonResponse(atualiza_oferta, status=400)

    return JsonResponse(atualiza_oferta, status=200)


@login_required
@require_POST
def responsavel(request, venda_id):
    venda = get_object_or_404(Venda, pk=venda_id, empresa=request.empresa)
    user = request.user
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'messages': {'__all__': ['JSON inválido']}}, status=400)

    usuario_id = data.get('usuario')
    responsavel = get_object_or_404(
        User.objects.select_related('agente__carteira', 'agente__equipe'),
        pk=usuario_id,
        agente__carteira__empresa=request.empresa,
        is_active=True
    )
    dados = { 'usuario' : responsavel.username }
    changes = ChangeTracker.verifica_alteracoes(venda, dados)
    if not changes:
        return JsonResponse(ResponsePattern.error('usuario_venda', ["Nenhuma mudança encontrada"]))

    update_agente = VendasService.update_agente_venda(venda, responsavel, user, changes)

    if not update_agente.get('success'):
        return JsonResponse(update_agente, status=400)

    return JsonResponse(update_agente, status=200)



# ── Adicionar comentário / HistVenda ─────────────────────────
@login_required
@require_POST
def comentario_e_esteira(request, venda_id):
    venda = get_object_or_404(Venda, pk=venda_id, empresa=request.empresa)
    user = request.user
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            ResponsePattern.error('json', ['JSON inválido']), status=400)

    nova_esteira = data.get('esteira')
    comentario = (data.get('comentario') or '').strip()

    esteira = get_object_or_404(Esteira, pk=nova_esteira, empresa=request.empresa, ativo=True)

    dados = {'esteira': esteira}
    alteracoes = ChangeTracker.verifica_alteracoes(venda, dados)
    if not alteracoes and not comentario:
        return JsonResponse(
            ResponsePattern.error('esteira', ["Comentário não pode ser vazio"]), status=400)

    if comentario:
        alteracoes.append(comentario)

    update_esteira = VendasService.update_esteira(venda, user, esteira, alteracoes)
    if not update_esteira['success']:
        return JsonResponse(update_esteira, status=400)

    # html = render_to_string(
    #     'relatorios/partials/timeline_hist.html',
    #     {'historico': update_esteira.get('data')},
    #     request=request
    # )
    return JsonResponse(
        ResponsePattern.success('esteira', ['✓ Movimentação registrada.']), status=201)



@require_GET
@login_required
def relatorio_vendas(request):
    """ Criar visualização por níveis de perfil """
    usuario = request.user
    service = RelatorioVendasService()
    params = request.GET.copy()
    params.pop('page', None)

    campos_permitidos = [
        'created_at__gte',
        'created_at__lte',
        'esteira_id',
        'oferta__produto_id',
        'oferta__parceiro_id',
        'esteira__carteira_id',
        'usuario_id'
    ]
    filtro = {
        k: v
        for k, v in params.dict().items()
        if k in campos_permitidos and v != ''
    }

    if not any(filtro.values()):
        hoje = timezone.now().date()
        filtro = {
            "created_at__gte": hoje.isoformat(),
            "created_at__lte": hoje.isoformat()
        }

    queryset = service.gerar(request.empresa, filtro, usuario)
    totais = service.calcular_totais(queryset)

    paginator = Paginator(queryset, 20)
    page = request.GET.get("page")
    vendas = paginator.get_page(page)

    context = service.get_context_relatorio(request.empresa, vendas, filtro, totais)
    context['query_string'] = params.urlencode()

    return render(request, 'relatorios/vendas.html', context)


@require_GET
@login_required
def agendas_list(request):
    from ..services.relatorio_agendas import RelatorioAgendaService
    usuario = request.user
    params = request.GET.copy()
    params.pop('page', None)

    service = RelatorioAgendaService()
    campos_permitidos = [
        'data_entrada__gte',
        'data_entrada__lte',
        'carteira_id',
        'situacao__tipo',
        'usuario_id',
        'modo',
        'agenda_ativa'
    ]
    filtro = {
        k: v
        for k, v in params.dict().items()
        if k in campos_permitidos and v != ''
    }

    if not any(filtro.values()):
        hoje = timezone.now().date()
        filtro = {
            "data_entrada__gte": hoje.isoformat(),
            "data_entrada__lte": hoje.isoformat()
        }

    queryset = service.gerar(request.empresa, filtro, usuario)
    totais = service.calcular_totais(queryset)

    paginator = Paginator(queryset, 20)
    page = request.GET.get("page")
    agendas = paginator.get_page(page)

    context = service.get_context_relatorio(request.empresa, agendas, filtro, totais)
    context['query_string'] = params.urlencode()

    return render(request, 'relatorios/agendas_list.html', context)


@login_required
@require_GET
def acionamentos_agenda(request, agenda_id):
    """Retorna JSON com os dados da agenda e seus acionamentos (drawer)."""

    try:
        agenda = (
            Agenda.objects
            .select_related('cliente', 'usuario', 'situacao', 'carteira')
            .get(pk=agenda_id, cliente__empresa=request.empresa)
        )
    except Agenda.DoesNotExist:
        return JsonResponse({'error': 'Agenda não encontrada'}, status=404)

    acionamentos = (
        Acionamento.objects
        .select_related('situacao')
        .filter(agenda=agenda)
        .order_by('-data_acionamento')
    )

    acionamentos_data = [
        {
            'situacao': a.situacao.nome,
            'tipo': a.situacao.tipo.lower(),
            'inicio': a.data_acionamento.strftime('%d/%m/%Y %H:%M'),
            'fim': a.data_finalizado.strftime('%d/%m/%Y %H:%M') if a.data_finalizado else None,
            'tempo_tela': a.tempo_tela_formatado,
            'comentario': a.comentario or '',
        }
        for a in acionamentos
    ]

    return JsonResponse({
        'cliente': agenda.cliente.nome,
        'agente': agenda.usuario.get_full_name() or agenda.usuario.username,
        'carteira': agenda.carteira_nome or (agenda.carteira.nome if agenda.carteira else '—'),
        'canal': agenda.canal,
        'situacao_atual': agenda.situacao.nome if agenda.situacao else '—',
        'ativa': agenda.agenda_ativa,
        'retorno': agenda.data_hora_retorno.strftime('%d/%m/%Y %H:%M')
        if agenda.data_hora_retorno else None,
        'acionamentos': acionamentos_data,
    })
