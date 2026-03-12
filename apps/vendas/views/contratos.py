from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from apps.vendas.forms import VendaForm
from apps.vendas.models import Venda, Parceiro, Produto, Oferta, Esteira
from apps.vendas.services.vendas_services import VendasService

@login_required
def registrar_venda(request):
    if request.method == "POST":
        venda_form = VendaForm(request.POST, prefix="venda", empresa=request.empresa)

        if venda_form.is_valid():
            usuario = request.user
            cliente_id = request.POST.get('cliente_id')
            id_agenda = request.POST.get('id_agenda')

            check_complements = VendasService.get_complements(
                usuario, cliente_id, id_agenda, request.empresa
            )
            if check_complements["success"]:
                venda = VendasService.registrar_venda(venda_form, check_complements["data"])
                return JsonResponse(venda, status=venda["status"])

            else:
                return JsonResponse(check_complements, status=400)


        form_errors = {"vendas": venda_form.errors}
        return JsonResponse({"success": False, "errors": form_errors}, status=400)

    context = {
        'venda_form': VendaForm(prefix="venda", empresa=request.empresa),
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