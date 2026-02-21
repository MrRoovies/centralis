from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Cliente
from .forms import ClienteForm
import json

# Create your views here.
@require_POST
@login_required
def search_cliente(request):
    if request.body:
        data = json.loads(request.body)
        documento = data.get("documento")
        cliente = Cliente.objects.filter(documento=documento)
        if cliente:
            return JsonResponse({'status': 'success', 'data': cliente }, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': "Cliente não existe"}, status=404)

@login_required
def cliente_novo(request):
    if request.method == "POST":
        cliente_form = ClienteForm(request.POST)
        if cliente_form.is_valid():
            cliente_form.save()
            return JsonResponse({"success": True, 'message': 'Cliente cadastrado com sucesso'})

        return JsonResponse({"success": False, "errors": cliente_form.errors}, status=400)

    form = ClienteForm()
    return render(request, 'clientes/cadastro-cliente.html', {"form": form})