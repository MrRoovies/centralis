from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from ..models import Endereco
from ..forms import EnderecoForm

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

@login_required
def novo_endereco(request, cliente_id):
    if request.method == "POST":
        endereco_form = EnderecoForm(request.POST, prefix="endereco")
        force = request.POST.get("force_reactivate")
        if endereco_form.is_valid():
            endereco_data = endereco_form.cleaned_data

            existente = Endereco.get_existente(
                cliente_id, endereco_data['cep'], endereco_data['tipo'])

            # CASO 1 — Já existe ativo
            if existente and existente.ativo:
                return JsonResponse({
                    "success": False,
                    "state": "nothing",
                    "errors": {
                        "endereco": {"__all__": ["Endereco já está cadastrado e ativo."]}
                    }
                }, status=400)

            # CASO 2 — Existe mas está inativo
            if existente and not existente.ativo:
                if force == "true":
                    existente.ativo = True
                    existente.save()
                    return JsonResponse({"success": True})

                return JsonResponse({
                    "success": False,
                    "state": "reactivate",
                    "email_id": existente.id,
                    "messages": {
                        "endereco": {"warning": ["Este endereco já existe, mas está inativo. Deseja reativar?"]}
                    }
                }, status=200)

            # CASO 3 — Não existe → criar
            with transaction.atomic():
                novo = endereco_form.save(commit=False)
                novo.cliente_id = cliente_id
                novo.save()

            return JsonResponse({
                "success": True,
                "message": {
                    "endereco": {"success": ["Endereco Criado com Sucesso!"]}
                }
            }, status=201)

        form_errors = {"email": endereco_form.errors}
        return JsonResponse({"success": False, "errors": form_errors}, status=400)

    form = EnderecoForm(prefix="endereco")
    context = {
        'title': "Criar novo Endereco",
        'action': "new_endereco",
        'form': form,
        'cliente_id': cliente_id
    }
    return render(request, 'components/modal.html', context)
