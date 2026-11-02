from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from apps.campanhas.services.discador_service import DiscadorService
from apps.clientes.models import Cliente, Telefone


@require_GET
@login_required
def disca(request, cliente_id):
    cliente = get_object_or_404(
        Cliente.objects.for_request(request)
        .prefetch_related(
            Prefetch('telefones', queryset=Telefone.objects.filter(ativo=True)),
        ),
        pk=cliente_id,
        empresa=request.empresa,
    )

    # Chamar discagem para cada telefone do 'proximo'
    discador = DiscadorService().inicia_discador(
        request.user, 
        cliente.telefones.all()
    )

    if not discador.get('success'):
        mensagens = {
            "success": False,
            "fim_da_fila": False,
            "messages": {
                "discador": {"error": [discador.get('message')]}
            }
        }
        return JsonResponse(mensagens, status=400)

    mensagens = {
        "success": True,
        "fim_da_fila": False,
        "messages": {
            "discador": {"success": ["Alguma coisa deu certo, finalmente"]}
        }
    }
    return JsonResponse(mensagens, status=200)