from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.models import User
from apps.vendas.models import Venda, Esteira, HistVenda, Oferta
from apps.core.responses.pattern import ResponsePattern
from apps.core.helpers.change_tracker import ChangeTracker
from apps.vendas.services.vendas_services import VendasService
import json

@login_required
@require_POST
def editar_valores(request, venda_id):
    venda = get_object_or_404(Venda, pk=venda_id, empresa=request.empresa)
    user = request.user
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        messages = ['JSON inválido']
        return JsonResponse(
            ResponsePattern.error("json", messages, status=400)
        )
    valores_e_formatos = VendasService.valores_e_formatos(data)

    if not valores_e_formatos.get('success'):
        return JsonResponse(valores_e_formatos, status=400)

    changes = ChangeTracker.verifica_alteracoes(venda, data)
    if not changes:
        return JsonResponse(ResponsePattern.error('valores_venda', ["Nenhuma mudanca encontrada"]), status=400)

    update = VendasService.update_valores(venda, valores_e_formatos['data'], user, changes)
    if not update.get('success'):
        return JsonResponse(update, status=400)

    return JsonResponse(update, status=200)


@login_required
@require_POST
def editar_oferta(request, venda_id):
    empresa = request.empresa
    venda = get_object_or_404(Venda, pk=venda_id, empresa=empresa)
    user = request.user

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(ResponsePattern.error('__all__', ['JSON inválido']), status=400)

    oferta_id = data.get('oferta')
    prazo = data.get('prazo')

    oferta = get_object_or_404(
        Oferta.objects.select_related('produto', 'parceiro'), pk=oferta_id, empresa=empresa)

    dados = {'oferta': oferta, 'prazo': prazo}
    alteracoes = ChangeTracker.verifica_alteracoes(venda, dados)
    if not alteracoes and prazo in [None, '']:
        return JsonResponse(
            ResponsePattern.error('esteira', ["Prazo não pode ser vazio.", "Nenhuma mudança encontrada"]),
            status=400)

    atualiza_oferta = VendasService.atualiza_oferta_prazo(venda, user, oferta, prazo, alteracoes)
    if not atualiza_oferta.get('success'):
        return JsonResponse(atualiza_oferta, status=400)

    return JsonResponse(atualiza_oferta, status=200)



@login_required
@require_POST
def responsavel(request, venda_id):
    venda = get_object_or_404(Venda, pk=venda_id, empresa=request.empresa)
    user = request.user
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'messages': {'__all__': ['JSON inválido']}}, status=400)

    usuario_id = data.get('usuario')
    agente_responsavel = get_object_or_404(
        User.objects.select_related('agente__carteira', 'agente__equipe'),
        pk=usuario_id,
        agente__carteira__empresa=request.empresa,
        is_active=True
    )
    dados = { 'usuario' : agente_responsavel }
    changes = ChangeTracker.verifica_alteracoes(venda, dados)
    if not changes:
        return JsonResponse(ResponsePattern.error('usuario_venda', ["Nenhuma mudança encontrada"]))

    update_agente = VendasService.update_agente_venda(venda, agente_responsavel, user, changes)

    if not update_agente.get('success'):
        return JsonResponse(update_agente, status=400)

    return JsonResponse(update_agente, status=200)


@login_required
@require_POST
def comentario_e_esteira(request, venda_id):
    venda = get_object_or_404(Venda, pk=venda_id, empresa=request.empresa)
    user = request.user
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            ResponsePattern.error('json', ['JSON inválido']), status=400)

    nova_esteira = data.get('esteira')
    comentario = (data.get('comentario') or '').strip()

    esteira = get_object_or_404(Esteira, pk=nova_esteira, empresa=request.empresa, ativo=True)

    dados = {'esteira': esteira}
    alteracoes = ChangeTracker.verifica_alteracoes(venda, dados)
    if not alteracoes and not comentario:
        return JsonResponse(
            ResponsePattern.error('esteira', ["Comentário não pode ser vazio"]), status=400)

    if comentario:
        alteracoes.append(comentario)

    update_esteira = VendasService.update_esteira(venda, user, esteira, alteracoes)
    if not update_esteira['success']:
        return JsonResponse(update_esteira, status=400)

    # html = render_to_string(
    #     'relatorios/partials/timeline_hist.html',
    #     {'historico': update_esteira.get('data')},
    #     request=request
    # )
    return JsonResponse(
        ResponsePattern.success('esteira', ['✓ Movimentação registrada.']), status=201)
