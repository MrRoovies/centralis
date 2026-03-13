from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from apps.campanhas.models import Campanha
import json


@login_required
@require_GET
# Lista as campanhas que o Agente esta habilitado
def painel_campanhas(request):
    campanhas = (Campanha.objects
         .filter(
            empresa=request.empresa,
            carteira=request.agente.carteira,
            distribuicao_ativa=True
         )
    )
    context = {
        "campanhas": campanhas
    }
    return render(request, "campanhas/campanhas.html", context)