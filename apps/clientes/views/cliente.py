from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from ..models import Cliente, Email, Telefone, Endereco
from django.db import transaction
from ..forms import ClienteForm, EmailForm, TelefoneForm
from django.contrib import messages
import json

# Create your views here.
@require_POST
@login_required
def search_cliente(request):
    if request.body:
        data = json.loads(request.body)
        documento = data.get("documento")

        cliente = Cliente.objects.for_request(request).filter(documento=documento).first()
        if not cliente:
            return JsonResponse({'status': 'error', 'message': "Cliente não existe"}, status=404)

        return JsonResponse({'status': 'success', 'data': cliente.id }, status=200)


@login_required
def cliente_novo(request):
    if request.method == "POST":
        cliente_form = ClienteForm(request.POST, prefix="cliente", empresa=request.empresa)
        email_form = EmailForm(request.POST, prefix="email")
        telefone_form = TelefoneForm(request.POST, prefix="telefone")

        if cliente_form.is_valid() and email_form.is_valid() and telefone_form.is_valid():
            with transaction.atomic():
                cliente = cliente_form.save(commit=False)
                cliente.empresa = request.empresa
                cliente = cliente_form.save()

                email = email_form.save(commit=False)
                email.cliente = cliente
                if email.email:
                    email.save()

                telefone = telefone_form.save(commit=False)
                telefone.cliente = cliente
                if telefone.telefone:
                    telefone.save()

            return JsonResponse({
                "success": True,
                "message": {
                    "cliente": {"success": ["Cliente criado com sucesso!"]}
                }
            }, status=200)

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
    return render(request, 'clientes/criar-cliente.html', forms)


@login_required
def cliente(request, id):
    cliente = get_object_or_404(
        Cliente.objects.for_request(request)
        .prefetch_related(
            Prefetch('emails', queryset=Email.objects.filter(ativo=True)),
            Prefetch('telefones', queryset=Telefone.objects.filter(ativo=True)),
            Prefetch('enderecos', queryset=Endereco.objects.filter(ativo=True))
        ),
        id=id
    )
    context = { "cliente": cliente }
    return render(request, 'clientes/cliente.html', context)


@login_required
def edita_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        # IMPORTANTE: passar instance aqui também
        cliente_form = ClienteForm(request.POST, instance=cliente, prefix="cliente")
        if cliente_form.is_valid():
            with transaction.atomic():
                edita_cli = cliente_form.save(commit=False)
                edita_cli.save()

            return JsonResponse({
                "success": True,
                "message": {
                    "cliente": {"success": ["Cliente alterado com Sucesso!"]}
                }
            }, status=200)

        form_errors = {
            "cliente": cliente_form.errors,
        }
        return JsonResponse({"success": False, "errors": form_errors}, status=400)


    form = ClienteForm(prefix="cliente", instance=cliente)
    context = {
        'title': "Editar Info's. Cliente",
        'action': "edit_client",
        'form': form,
        'cliente_id': cliente_id
    }
    return render(request, 'components/modal.html', context)


@require_GET
@login_required
def atendimento_cliente(request, cliente_id):
    from apps.agenda.services.agenda_services import AgendamentoService
    from apps.agenda.models import Situacao
    usuario = request.user

    nova_agenda = AgendamentoService().criar_ou_atualizar(cliente_id, usuario)
    if not nova_agenda['success']:
        messages.error(request, nova_agenda['errors'])
        return redirect(f'/clientes/cliente/{cliente_id}')

    cliente = get_object_or_404(
        Cliente.objects.for_request(request)
        .prefetch_related(
            Prefetch('emails', queryset=Email.objects.filter(ativo=True)),
            Prefetch('telefones', queryset=Telefone.objects.filter(ativo=True)),
            Prefetch('enderecos', queryset=Endereco.objects.filter(ativo=True))
        ),
        id=cliente_id
    )
    situacoes = Situacao.objects.exclude(ativo=False)
    messages.success(request, nova_agenda['message'])
    context = {
        "cliente": cliente,
        "situacoes": situacoes,
        "nova_agenda": nova_agenda
    }
    return render(request, 'clientes/atendimento_cliente.html', context)
