from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Cliente
from django.db import transaction
from .forms import ClienteForm, EmailForm, TelefoneForm
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
        cliente_form = ClienteForm(request.POST, prefix="cliente")
        email_form = EmailForm(request.POST, prefix="email")
        telefone_form = TelefoneForm(request.POST, prefix="telefone")

        if cliente_form.is_valid() and email_form.is_valid() and telefone_form.is_valid():
            with transaction.atomic():
                cliente = cliente_form.save()

                email = email_form.save(commit=False)
                email.cliente = cliente
                telefone = telefone_form.save(commit=False)
                telefone.cliente = cliente

            return JsonResponse({"success": True, 'message': 'Cliente cadastrado com sucesso'})

        form_errors = {
            "cliente": cliente_form.errors,
            "email": email_form.errors,
            "telefone": telefone_form.errors
        }
        return JsonResponse({"success": False, "errors": form_errors}, status=400)

    forms = {
        'cliente_form' : ClienteForm(prefix="cliente"),
        'email_form' : EmailForm(prefix="email"),
        'telefone_form' : TelefoneForm(prefix="telefone")
    }
    return render(request, 'clientes/cadastro-cliente.html', forms)