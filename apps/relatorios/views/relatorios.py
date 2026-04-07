import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.relatorio_vendas import FiltroRelatorioVendas, RelatorioVendasService
from django.utils import timezone
from datetime import datetime, time
from django.core.paginator import Paginator

@login_required
def relatorio_vendas(request):
    data = request.GET.copy()

    if not data:
        hoje = timezone.now().date()
        data = {
            "data_inicio": hoje.isoformat(),
            "data_fim": hoje.isoformat()
        }

    filtro = FiltroRelatorioVendas(data)

    vendas = RelatorioVendasService().gerar(request.empresa, filtro)
    totais = RelatorioVendasService().calcular_totais(vendas)


    paginator = Paginator(vendas, 50)
    page = request.GET.get("page")
    vendas = paginator.get_page(page)

    context = RelatorioVendasService().get_context_relatorio(request.empresa, vendas, totais, filtro)

    return render(request, 'relatorios/vendas.html', context)
