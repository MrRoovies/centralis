from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.db import transaction
import json

from apps.vendas.models import Parceiro, Produto, Oferta, Esteira
from apps.usuarios.models import Carteira
from apps.core.choices import TipoEsteira
from apps.core.responses.pattern import ResponsePattern


# ════════════════════════════════════════════════════════════
# PÁGINA PRINCIPAL
# ════════════════════════════════════════════════════════════

@login_required
@require_GET
def lista_vendas_admin(request):
    empresa = request.empresa

    parceiros = Parceiro.objects.filter(empresa=empresa).order_by('nome')
    produtos  = Produto.objects.filter(empresa=empresa).order_by('nome')
    ofertas   = (
        Oferta.objects
        .filter(empresa=empresa)
        .select_related('produto', 'parceiro')
        .order_by('produto__nome', 'parceiro__nome')
    )
    esteiras  = (
        Esteira.objects
        .filter(empresa=empresa)
        .select_related('carteira')
        .order_by('carteira__nome', 'ordem')
    )
    carteiras = Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome')

    context = {
        'parceiros':  parceiros,
        'produtos':   produtos,
        'ofertas':    ofertas,
        'esteiras':   esteiras,
        'carteiras':  carteiras,
        'tipo_choices': TipoEsteira.choices,
    }
    return render(request, 'vendas/vendas_admin.html', context)


# ════════════════════════════════════════════════════════════
# PARCEIROS
# ════════════════════════════════════════════════════════════

@login_required
def parceiro_detail(request, parceiro_id=None):
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(ResponsePattern.error('parceiro', ['JSON inválido']), status=400)

        nome = (data.get('nome') or '').strip()
        if not nome:
            return JsonResponse(ResponsePattern.error('parceiro', ['Nome é obrigatório.']), status=400)

        ativo = data.get('ativo', True)

        try:
            with transaction.atomic():
                if parceiro_id:
                    parceiro = get_object_or_404(Parceiro, pk=parceiro_id, empresa=empresa)
                    parceiro.nome  = nome
                    parceiro.ativo = ativo
                    parceiro.save()
                    msg = '✓ Parceiro atualizado com sucesso!'
                else:
                    Parceiro.objects.create(empresa=empresa, nome=nome, ativo=ativo)
                    msg = '✓ Parceiro criado com sucesso!'

            return JsonResponse(ResponsePattern.success('parceiro', [msg]), status=200)

        except Exception as e:
            return JsonResponse(ResponsePattern.error('parceiro', [str(e)]), status=400)

    # GET
    data = {}
    if parceiro_id:
        p = get_object_or_404(Parceiro, pk=parceiro_id, empresa=empresa)
        data = {'parceiro': {'nome': p.nome, 'ativo': p.ativo}}
    else:
        data = {'parceiro': {}}
    return JsonResponse(data)


@login_required
@require_POST
def parceiro_toggle(request, parceiro_id):
    parceiro = get_object_or_404(Parceiro, pk=parceiro_id, empresa=request.empresa)
    parceiro.ativo = not parceiro.ativo
    parceiro.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': parceiro.ativo,
        'messages': {'parceiro': {'success': [f'Parceiro {"ativado" if parceiro.ativo else "desativado"}!']}}
    })


# ════════════════════════════════════════════════════════════
# PRODUTOS
# ════════════════════════════════════════════════════════════

@login_required
def produto_detail(request, produto_id=None):
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(ResponsePattern.error('produto', ['JSON inválido']), status=400)

        nome = (data.get('nome') or '').strip()
        if not nome:
            return JsonResponse(ResponsePattern.error('produto', ['Nome é obrigatório.']), status=400)

        ativo = data.get('ativo', True)

        try:
            with transaction.atomic():
                if produto_id:
                    produto = get_object_or_404(Produto, pk=produto_id, empresa=empresa)
                    produto.nome  = nome
                    produto.ativo = ativo
                    produto.save()
                    msg = '✓ Produto atualizado com sucesso!'
                else:
                    Produto.objects.create(empresa=empresa, nome=nome, ativo=ativo)
                    msg = '✓ Produto criado com sucesso!'

            return JsonResponse(ResponsePattern.success('produto', [msg]), status=200)

        except Exception as e:
            return JsonResponse(ResponsePattern.error('produto', [str(e)]), status=400)

    # GET
    data = {}
    if produto_id:
        p = get_object_or_404(Produto, pk=produto_id, empresa=empresa)
        data = {'produto': {'nome': p.nome, 'ativo': p.ativo}}
    else:
        data = {'produto': {}}
    return JsonResponse(data)


@login_required
@require_POST
def produto_toggle(request, produto_id):
    produto = get_object_or_404(Produto, pk=produto_id, empresa=request.empresa)
    produto.ativo = not produto.ativo
    produto.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': produto.ativo,
        'messages': {'produto': {'success': [f'Produto {"ativado" if produto.ativo else "desativado"}!']}}
    })


# ════════════════════════════════════════════════════════════
# OFERTAS
# ════════════════════════════════════════════════════════════

@login_required
def oferta_detail(request, oferta_id=None):
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(ResponsePattern.error('oferta', ['JSON inválido']), status=400)

        parceiro_id = data.get('parceiro_id')
        produto_id  = data.get('produto_id')
        prazo_min   = data.get('prazo_min')
        prazo_max   = data.get('prazo_max')
        comissao    = data.get('comissao')
        ativo       = data.get('ativo', True)

        if not all([parceiro_id, produto_id, prazo_min, prazo_max, comissao]):
            return JsonResponse(
                ResponsePattern.error('oferta', ['Preencha todos os campos obrigatórios.']),
                status=400
            )

        try:
            prazo_min = int(prazo_min)
            prazo_max = int(prazo_max)
            if prazo_min <= 0 or prazo_max <= 0:
                raise ValueError
            if prazo_min > prazo_max:
                return JsonResponse(
                    ResponsePattern.error('oferta', ['Prazo mínimo não pode ser maior que o máximo.']),
                    status=400
                )
        except (ValueError, TypeError):
            return JsonResponse(
                ResponsePattern.error('oferta', ['Prazos devem ser números inteiros positivos.']),
                status=400
            )

        parceiro = get_object_or_404(Parceiro, pk=parceiro_id, empresa=empresa)
        produto  = get_object_or_404(Produto,  pk=produto_id,  empresa=empresa)

        try:
            with transaction.atomic():
                if oferta_id:
                    oferta = get_object_or_404(Oferta, pk=oferta_id, empresa=empresa)
                    oferta.parceiro  = parceiro
                    oferta.produto   = produto
                    oferta.prazo_min = prazo_min
                    oferta.prazo_max = prazo_max
                    oferta.comissao  = comissao
                    oferta.ativo     = ativo
                    oferta.save()
                    msg = '✓ Oferta atualizada com sucesso!'
                else:
                    Oferta.objects.create(
                        empresa=empresa,
                        parceiro=parceiro,
                        produto=produto,
                        prazo_min=prazo_min,
                        prazo_max=prazo_max,
                        comissao=comissao,
                        ativo=ativo,
                    )
                    msg = '✓ Oferta criada com sucesso!'

            return JsonResponse(ResponsePattern.success('oferta', [msg]), status=200)

        except Exception as e:
            return JsonResponse(ResponsePattern.error('oferta', [str(e)]), status=400)

    # GET
    parceiros = list(Parceiro.objects.filter(empresa=empresa, ativo=True).values('id', 'nome').order_by('nome'))
    produtos  = list(Produto.objects.filter(empresa=empresa, ativo=True).values('id', 'nome').order_by('nome'))

    data = {
        'parceiros': parceiros,
        'produtos':  produtos,
        'oferta': {},
    }

    if oferta_id:
        o = get_object_or_404(Oferta.objects.select_related('parceiro', 'produto'), pk=oferta_id, empresa=empresa)
        data['oferta'] = {
            'parceiro_id': o.parceiro_id,
            'produto_id':  o.produto_id,
            'prazo_min':   o.prazo_min,
            'prazo_max':   o.prazo_max,
            'comissao':    str(o.comissao),
            'ativo':       o.ativo,
        }

    return JsonResponse(data)


@login_required
@require_POST
def oferta_toggle(request, oferta_id):
    oferta = get_object_or_404(Oferta, pk=oferta_id, empresa=request.empresa)
    oferta.ativo = not oferta.ativo
    oferta.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': oferta.ativo,
        'messages': {'oferta': {'success': [f'Oferta {"ativada" if oferta.ativo else "desativada"}!']}}
    })


# ════════════════════════════════════════════════════════════
# ESTEIRAS
# ════════════════════════════════════════════════════════════

@login_required
def esteira_detail(request, esteira_id=None):
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(ResponsePattern.error('esteira', ['JSON inválido']), status=400)

        nome        = (data.get('nome') or '').strip()
        carteira_id = data.get('carteira_id')
        tipo        = data.get('tipo', '').strip()
        ordem       = data.get('ordem', 1)
        ativo       = data.get('ativo', True)

        if not all([nome, carteira_id, tipo]):
            return JsonResponse(
                ResponsePattern.error('esteira', ['Nome, carteira e tipo são obrigatórios.']),
                status=400
            )

        try:
            ordem = int(ordem)
            if ordem < 1:
                raise ValueError
        except (ValueError, TypeError):
            ordem = 1

        carteira = get_object_or_404(Carteira, pk=carteira_id, empresa=empresa, ativo=True)

        try:
            with transaction.atomic():
                if esteira_id:
                    esteira = get_object_or_404(Esteira, pk=esteira_id, empresa=empresa)
                    esteira.nome     = nome
                    esteira.carteira = carteira
                    esteira.tipo     = tipo
                    esteira.ordem    = ordem
                    esteira.ativo    = ativo
                    esteira.save()
                    msg = '✓ Esteira atualizada com sucesso!'
                else:
                    Esteira.objects.create(
                        empresa=empresa,
                        nome=nome,
                        carteira=carteira,
                        tipo=tipo,
                        ordem=ordem,
                        ativo=ativo,
                    )
                    msg = '✓ Esteira criada com sucesso!'

            return JsonResponse(ResponsePattern.success('esteira', [msg]), status=200)

        except Exception as e:
            return JsonResponse(ResponsePattern.error('esteira', [str(e)]), status=400)

    # GET
    carteiras = list(Carteira.objects.filter(empresa=empresa, ativo=True).values('id', 'nome').order_by('nome'))

    data = {
        'carteiras':     carteiras,
        'tipo_choices':  TipoEsteira.choices,
        'esteira': {},
    }

    if esteira_id:
        e = get_object_or_404(Esteira.objects.select_related('carteira'), pk=esteira_id, empresa=empresa)
        data['esteira'] = {
            'nome':        e.nome,
            'carteira_id': e.carteira_id,
            'tipo':        e.tipo,
            'ordem':       e.ordem,
            'ativo':       e.ativo,
        }

    return JsonResponse(data)


@login_required
@require_POST
def esteira_toggle(request, esteira_id):
    esteira = get_object_or_404(Esteira, pk=esteira_id, empresa=request.empresa)
    esteira.ativo = not esteira.ativo
    esteira.save(update_fields=['ativo'])
    return JsonResponse({
        'success': True,
        'ativo': esteira.ativo,
        'messages': {'esteira': {'success': [f'Esteira {"ativada" if esteira.ativo else "desativada"}!']}}
    })