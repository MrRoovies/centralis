from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from ..models import Endereco
#from ..forms import EnderecoForm

@require_POST
@login_required
def delete_endereco(request, id):
    endereco = get_object_or_404(Endereco, id=id)
    endereco.ativo = False
    endereco.save()
    return JsonResponse({
        "success": True,
        "state": "nothing",
        "messages": {
            "endereco": {"success": ["Endereco deletado com sucesso."]}
        }
    }, status=200)

