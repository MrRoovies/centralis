import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.db import IntegrityError

from apps.clientes.models import Bancos


def _campos_obrigatorios(data):
    erros = {}
    for campo in ('cod_banco', 'nome_banco'):
        if not str(data.get(campo, '')).strip():
            erros[campo] = [f'Campo obrigatório.']
    if erros:
        return {'success': False, 'messages': {'banco': erros}}
    return None


@login_required
@require_GET
def referencias(request):
    """Tela principal de configurações (aba Bancos + tabs futuras)."""
    bancos = Bancos.objects.all().order_by('cod_banco')
    return render(request, 'referencias/principal.html', {'bancos': bancos})


@login_required
def banco_detail(request, banco_id=None):
    """
    GET  → dados do banco para preencher o drawer (ou defaults para novo).
    POST → criar ou editar.
    """
    if request.method == 'GET':
        if banco_id:
            banco = get_object_or_404(Bancos, id=banco_id)
            return JsonResponse({
                'banco': {
                    'id': banco.id,
                    'cod_banco': banco.cod_banco,
                    'nome_banco': banco.nome_banco
                }
            })
        # Novo
        return JsonResponse({'banco': {
            'id': None,
            'cod_banco': '',
            'nome_banco': ''
        }})

    # POST
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'messages': {'banco': {'__all__': ['JSON inválido']}}},
            status=400
        )

    erro = _campos_obrigatorios(data)
    if erro:
        return JsonResponse(erro, status=400)

    cod_banco  = data['cod_banco'].strip().upper()
    nome_banco = data['nome_banco'].strip()

    try:
        if banco_id:
            banco = get_object_or_404(Bancos, id=banco_id)
            banco.cod_banco  = cod_banco
            banco.nome_banco = nome_banco
            banco.save()
            msg = 'Banco atualizado com sucesso.'
        else:
            banco = Bancos.objects.create(
                cod_banco=cod_banco,
                nome_banco=nome_banco
            )
            msg = 'Banco cadastrado com sucesso.'
    except IntegrityError:
        return JsonResponse(
            {'success': False, 'messages': {'banco': {
                '__all__': ['Já existe um banco com este código e nome.']
            }}},
            status=400
        )

    return JsonResponse({
        'success': True,
        'msg': msg,
        'banco': {
            'id':        banco.id,
            'cod_banco': banco.cod_banco,
            'nome_banco': banco.nome_banco
        }
    })