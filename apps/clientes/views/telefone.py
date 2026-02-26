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

@login_required
def novo_telefone(request, cliente_id):
    if request.method == "POST":
        telefone_form = TelefoneForm(request.POST, prefix="telefone")
        force = request.POST.get("force_reactivate")
        if telefone_form.is_valid():
            telefone_data = telefone_form.cleaned_data
            existente = Telefone.get_existente(cliente_id, telefone_data['telefone'], telefone_data['tipo'])

            # CASO 1 — Já existe ativo
            if existente and existente.ativo:
                return JsonResponse({
                    "success": False,
                    "state": "nothing",
                    "errors": {
                        "telefone": {"__all__": ["Telefone já está cadastrado e ativo."]}
                    }
                }, status=400)

            # CASO 2 — Existe mas está inativo
            if existente and not existente.ativo:
                if force == "true":
                    existente.ativo = True
                    existente.whats_app = telefone_data['whats_app']
                    existente.save()
                    return JsonResponse({"success": True})

                return JsonResponse({
                    "success": False,
                    "state": "reactivate",
                    "email_id": existente.id,
                    "messages": {
                        "email": {"warning": ["Este telefone já existe, mas está inativo. Deseja reativar?"]}
                    }
                }, status=200)

            # CASO 3 — Não existe → criar
            with transaction.atomic():
                novo = telefone_form.save(commit=False)
                novo.cliente_id = cliente_id
                novo.save()

            return JsonResponse({
                "success": True,
                "message": {
                    "telefone": {"success": ["Telefone Criado com Sucesso!"]}
                }
            }, status=201)

        form_errors = {"email": telefone_form.errors}
        return JsonResponse({"success": False, "errors": form_errors}, status=400)

    form = TelefoneForm(prefix="telefone")
    context = {
        'title': "Criar novo Telefone",
        'action': "new_fone",
        'form': form,
        'cliente_id': cliente_id
    }
    return render(request, 'components/modal.html', context)
