from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db import transaction, DatabaseError
from ..models import Agenda
import json

@require_GET
@login_required
def hist_agenda_cliente(request, cliente_id):
    agendas = Agenda.objects.filter(cliente_id=cliente_id).order_by("-id")
    context = {
        "agendas": agendas
    }
    return render(request, "agendas/agenda_detalhes.html", context)
