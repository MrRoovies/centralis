from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import datetime, time
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.models import User
from apps.agenda.models import Agenda, Acionamento
from apps.vendas.models import Venda, Parceiro, Produto, Oferta, Esteira
from ..services.relatorio_agendas import RelatorioAgendaService
from ..services.relatorio_vendas import RelatorioVendasService


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

    usuarios = User.objects.prefetch_related('agente').filter(
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


@require_GET
@login_required
def agendas_list(request):
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
        hoje = timezone.localdate()

        inicio = timezone.make_aware(datetime.combine(hoje, time.min))
        fim = timezone.make_aware(datetime.combine(hoje, time.max))

        filtro["data_entrada__gte"] = inicio
        filtro["data_entrada__lte"] = fim

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
