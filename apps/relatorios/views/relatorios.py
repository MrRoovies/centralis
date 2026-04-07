import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..services.relatorio_vendas import FiltroRelatorioVendas, RelatorioVendasService
from django.utils import timezone
from datetime import datetime, time

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
    context = RelatorioVendasService().get_context_relatorio(request.empresa, vendas, filtro)

    return render(request, 'relatorios/vendas.html', context)
