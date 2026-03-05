from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from ..models import Agenda
from ..services.agenda_services import AgendamentoService
import json

@require_GET
@login_required
def hist_agenda_cliente(request, cliente_id):
    agendas = Agenda.objects.filter(cliente_id=cliente_id).order_by("-id")
    context = {
        "agendas": agendas
    }
    return render(request, "agendas/agenda_detalhes.html", context)

@require_POST
@login_required
def registrar_atendimento(request):
    if request.body:
        data = json.loads(request.body)
        id_agenda = data.get('id_agenda')
        situacao = data.get('situacao')
        dataAgenda = data.get('dataAgenda')
        telefone = data.get('telefone')
        comentario = data.get('comentario')

        agendamento = AgendamentoService().registrar_situacao(
            id_agenda,
            situacao,
            dataAgenda,
            telefone,
            comentario
        )
        if not agendamento['success']:
            return JsonResponse(agendamento, status=404)

        else:
            return JsonResponse(agendamento, status=200)
    else:
        return JsonResponse({
            "success": False,
            "messages": {
                "agenda": {"error": ["Nada Recebido."]}
            }
        }, status=400)









