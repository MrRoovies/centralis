from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db import transaction
from apps.vendas.forms import VendaForm
from apps.vendas.models import Venda
# Create your views here.

def registrar_venda(request):
    context = {
        'venda_form': VendaForm(prefix="venda"),
        'cliente_id': ""
    }
    return render(request, 'vendas/registrar_venda.html', context)