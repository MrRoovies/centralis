from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from ..services.relatorio_vendas import RelatorioVendasService
from django.utils import timezone
from django.core.paginator import Paginator
from apps.agenda.models import Agenda, Acionamento

from ...vendas.models import Venda

@require_GET
@login_required
def detalhe_venda(request, id):
    venda = get_object_or_404(
        Venda.objects.select_related('cliente', 'esteira').prefetch_related('historico__esteira', 'historico__usuario'),
        pk=id,
        empresa=request.empresa
    )

    historico = [
        {
            'esteira': h.esteira.nome,
            'usuario': h.usuario.get_full_name() or h.usuario.username,
            'data': h.data.strftime('%d/%m/%Y %H:%M'),
            'comentario': h.comentario or '',
        }
        for h in venda.historico.order_by('data')
    ]

    return JsonResponse({
        'contrato': venda.contrato,
        'cliente': venda.cliente.nome,
        'produto': venda.produto_nome,
        'parceiro': venda.parceiro_nome,
        'valor': f'{venda.valor:,.2f}',
        'historico': historico,
    })


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
