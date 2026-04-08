from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from ..services.relatorio_vendas import FiltroRelatorioVendas, RelatorioVendasService
from django.utils import timezone
from django.core.paginator import Paginator

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
    data = request.GET.copy()
    usuario = request.user

    if not data:
        hoje = timezone.now().date()
        data = {
            "data_inicio": hoje.isoformat(),
            "data_fim": hoje.isoformat()
        }

    filtro = FiltroRelatorioVendas(data)

    vendas = RelatorioVendasService().gerar(request.empresa, filtro, usuario)
    totais = RelatorioVendasService().calcular_totais(vendas)


    paginator = Paginator(vendas, 50)
    page = request.GET.get("page")
    vendas = paginator.get_page(page)

    context = RelatorioVendasService().get_context_relatorio(request.empresa, vendas, totais, filtro)

    return render(request, 'relatorios/vendas.html', context)