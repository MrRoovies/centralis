from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from ..models import Email
from ..forms import EmailForm

@require_POST
@login_required
def deleta_email(request, id):
    email = get_object_or_404(Email, id=id)
    email.ativo = False
    email.save()
    return JsonResponse({
        "success": True,
        "state": "nothing",
        "messages": {
            "email": {"success": ["E-mail deletado com sucesso."]}
        }
    }, status=200)

@login_required
def novo_email(request, cliente_id):
    if request.method == "POST":
        email_form = EmailForm(request.POST, prefix="email")
        force = request.POST.get("force_reactivate")
        if email_form.is_valid():
            email_data = email_form.cleaned_data

            existente = Email.get_existente(
                cliente_id, email_data["email"], email_data["tipo"]
            )

            # CASO 1 — Já existe ativo
            if existente and existente.ativo:
                return JsonResponse({
                    "success": False,
                    "state": "nothing",
                    "errors": {
                        "email": {"__all__": ["Este e-mail já está cadastrado e ativo."]}
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
                        "email": {"warning": ["Este e-mail já existe, mas está inativo. Deseja reativar?"]}
                    }
                }, status=200)

            # CASO 3 — Não existe → criar
            with transaction.atomic():
                novo = email_form.save(commit=False)
                novo.cliente_id = cliente_id
                novo.save()

            return JsonResponse({
                "success": True,
                "message": {
                        "email": {"success": ["E-mail Criado com Sucesso!"]}
                    }
            }, status=201)

        form_errors = {"email": email_form.errors}
        return JsonResponse({"success": False, "errors": form_errors}, status=400)

    form = EmailForm(prefix="email")
    context = {
        'title': "Criar novo E-mail",
        'action': "new_mail",
        'form': form,
        'cliente_id': cliente_id
    }
    return render(request, 'components/modal.html', context)

