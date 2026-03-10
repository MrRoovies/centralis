from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db import transaction
from apps.vendas.forms import VendaForm
from apps.vendas.models import Venda, Parceiro, Produto, Oferta
# Create your views here.

def registrar_venda(request):
    context = {
        'venda_form': VendaForm(prefix="venda"),
        'cliente_id': ""
    }
    return render(request, 'vendas/registrar_venda.html', context)

@require_GET
@login_required
def get_parceiros(request):
    parceiros = Parceiro.objects.filter(
        empresa=request.empresa,
        ativo=True
    ).values('id', 'nome')

    return JsonResponse({'parceiros': list(parceiros)})


@require_GET
@login_required
def get_produtos(request):
    parceiro_id = request.GET.get('parceiro_id')

    produtos = Produto.objects.filter(
        empresa=request.empresa,
        ativo=True,
        ofertas__parceiro_id=parceiro_id  # só produtos que têm oferta com esse parceiro
    ).distinct().values('id', 'nome')

    return JsonResponse({'produtos': list(produtos)})


@require_GET
@login_required
def get_ofertas(request):
    parceiro_id = request.GET.get('parceiro_id')
    produto_id = request.GET.get('produto_id')

    ofertas = Oferta.objects.filter(
        empresa=request.empresa,
        ativo=True,
        parceiro_id=parceiro_id,
        produto_id=produto_id
    ).values('id', 'prazo_min', 'prazo_max', 'comissao')

    # monta um label legível para o select
    data = [
        {
            'id': o['id'],
            'nome': f"{o['prazo_min']} a {o['prazo_max']} meses"
        }
        for o in ofertas
    ]

    return JsonResponse({'ofertas': data})