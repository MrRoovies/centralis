from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from ..models import Telefone
from ..forms import TelefoneForm

@require_POST
@login_required
def deleta_telefone(request, id):
    telefone = get_object_or_404(Telefone, id=id)
    telefone.ativo = False
    telefone.save()
    return JsonResponse({
        "success": True,
        "state": "nothing",
        "messages": {
            "telefone": {"success": ["Telefone deletado com sucesso."]}
        }
    }, status=200)

