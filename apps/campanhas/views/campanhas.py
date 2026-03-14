from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from apps.campanhas.models import Campanha, CampanhaAgente
import json


@login_required
@require_GET
# Lista as campanhas que o Agente esta habilitado
def painel_campanhas(request):
    usuario = request.user
    campanhas = (CampanhaAgente.objects
        .select_related('campanha', 'campanha__carteira')
        .filter(
            agente=usuario.agente,
            campanha__distribuicao_ativa=True,
            campanha__empresa=request.empresa,
            campanha__carteira=usuario.agente.carteira,
        )
    )
    context = {
        "campanhas_agente": campanhas
    }
    return render(request, "campanhas/campanhas.html", context)


@login_required
@require_GET
def atender(request, id):
    pass