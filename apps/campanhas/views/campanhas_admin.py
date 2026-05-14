from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q
import json
from apps.clientes.models import Cliente
from apps.campanhas.models import Campanha, CampanhaAgente, CampanhaCliente
from apps.agenda.models import Situacao
from apps.usuarios.models import Agente, Carteira
from apps.core.choices import ModoAtendimento, OrdemSorteio
from apps.campanhas.services.campanha_services import CampanhasAdmin
from apps.core.responses.pattern import ResponsePattern


@login_required
@require_GET
def lista_campanhas_admin(request):
    """Tela principal de gestão de campanhas."""
    empresa = request.empresa
    params = request.GET.copy()
    params.pop('page', None)

    campos_permitidos = [
        'carteira_id',
        'modo_atendimento',
        'distribuicao_ativa',
        'nome__icontains',
    ]
    filtro = {
        k: v
        for k, v in params.dict().items()
        if k in campos_permitidos and v != ''
    }

    queryset = CampanhasAdmin.lista_campanhas(empresa, filtro)

    counts = queryset.aggregate(
        total=Count('id'),
        ativas=Count('id', filter=Q(distribuicao_ativa=True))
    )
    total = counts['total']
    ativas = counts['ativas']
    inativas = total - ativas

    paginator = Paginator(queryset, 20)
    campanhas = paginator.get_page(request.GET.get('page'))

    context = {
        'campanhas': campanhas,
        'carteiras': Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
        'modos': [{'value': m[0], 'label': m[1]} for m in ModoAtendimento.choices],
        'ordens': [{'value': o[0], 'label': o[1]} for o in OrdemSorteio.choices],
        'filtros': filtro,
        'total': total,
        'ativas': ativas,
        'inativas': inativas,
        'query_string': params.urlencode(),
    }
    return render(request, 'campanhas/campanhas_admin.html', context)


@login_required
def campanha_detail(request, campanha_id=None):
    """GET → dados da campanha | POST → criar ou editar."""
    empresa = request.empresa

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                ResponsePattern.error('campanha', ['JSON inválido']), status=400
            )

        nome = (data.get('nome') or '').strip()
        carteira_id = data.get('carteira_id')
        modo_atendimento = data.get('modo_atendimento')
        metodo_distribuicao = data.get('metodo_distribuicao')
        msg_whatsapp = data.get('msg_whatsapp')
        distribuicao_ativa = data.get('distribuicao_ativa', True)

        if not all([nome, carteira_id, modo_atendimento, metodo_distribuicao]):
            return JsonResponse(
                ResponsePattern.error('campanha', ['Preencha todos os campos obrigatórios.']),
                status=400)

        save_campanha = CampanhasAdmin.cria_ou_edita(
            carteira_id,
            campanha_id,
            nome,
            modo_atendimento,
            metodo_distribuicao,
            distribuicao_ativa,
            msg_whatsapp,
            empresa
        )
        if not save_campanha.get('success'):
            return JsonResponse(save_campanha, status=400)

        return JsonResponse(save_campanha, status=201)

    # GET
    get_campanha = CampanhasAdmin.get_campanha(campanha_id, empresa)
    return JsonResponse(get_campanha.get('data'), status=200)


@login_required
@require_POST
def toggle_campanha(request, campanha_id):
    """Ativa/desativa distribuição da campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)
    campanha.distribuicao_ativa = not campanha.distribuicao_ativa
    campanha.save(update_fields=['distribuicao_ativa'])
    return JsonResponse({
        'success': True,
        'distribuicao_ativa': campanha.distribuicao_ativa,
        'messages': {
            'campanha': {'success': [
                f'Campanha {"ativada" if campanha.distribuicao_ativa else "desativada"}!'
            ]}
        }
    })


# ════════════════════════════════════════════════════════════
# AGENTES — vincular / listar / desvincular
# ════════════════════════════════════════════════════════════

@login_required
@require_GET
def agentes_campanha(request, campanha_id):
    """Retorna agentes vinculados e disponíveis para a campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)

    vinculados_qs = (
        CampanhaAgente.objects
        .filter(campanha=campanha, ativo=True)
        .select_related('agente__usuario', 'agente__perfil')
    )

    vinculados = [
        {
            'id': ca.agente.id,
            'nome': ca.agente.usuario.get_full_name() or ca.agente.usuario.username,
            'perfil': ca.agente.perfil.get_codigo_display() if ca.agente.perfil else '',
            'ativo': ca.ativo,
        }
        for ca in vinculados_qs
    ]

    ids_vinculados = {ca.agente.id for ca in vinculados_qs}

    disponiveis = [
        {
            'id': a.id,
            'nome': a.usuario.get_full_name() or a.usuario.username,
        }
        for a in Agente.objects.filter(
            carteira=campanha.carteira,
            usuario__is_active=True
        ).select_related('usuario').exclude(id__in=ids_vinculados)
    ]

    return JsonResponse({'vinculados': vinculados, 'disponiveis': disponiveis})


@login_required
@require_POST
def vincular_agente(request, campanha_id):
    """Vincula um agente à campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)

    try:
        data = json.loads(request.body)
        agente_id = data.get('agente_id')
    except json.JSONDecodeError:
        return JsonResponse(ResponsePattern.error('agente', ['JSON inválido']), status=400)

    agente = get_object_or_404(
        Agente, pk=agente_id, carteira=campanha.carteira
    )

    obj, created = CampanhaAgente.objects.get_or_create(
        campanha=campanha,
        agente=agente,
        defaults={'ativo': True}
    )
    if not created:
        obj.ativo = True
        obj.save(update_fields=['ativo'])

    return JsonResponse(
        ResponsePattern.success('agente', ['✓ Agente vinculado!']), status=200
    )


@login_required
@require_POST
def desvincular_agente(request, campanha_id, agente_id):
    """Remove o vínculo do agente com a campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)
    agente = get_object_or_404(Agente, pk=agente_id)

    CampanhaAgente.objects.filter(campanha=campanha, agente=agente).update(ativo=False)

    return JsonResponse(
        ResponsePattern.success('agente', ['Agente desvinculado.']), status=200
    )


# ════════════════════════════════════════════════════════════
# MAILING — adicionar cliente individual / importar CSV / resumo
# ════════════════════════════════════════════════════════════

@login_required
@require_POST
def adicionar_cliente_mailing(request, campanha_id):
    """Adiciona um cliente individualmente ao mailing da campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)

    try:
        data = json.loads(request.body)
        cliente_id = data.get('cliente_id')
    except json.JSONDecodeError:
        return JsonResponse(ResponsePattern.error('mailing', ['JSON inválido']), status=400)

    cliente = get_object_or_404(Cliente, pk=cliente_id, empresa=request.empresa)

    situacao_inicial = campanha.carteira.situacoes.filter(
        tipo='INICIAL'
    ).first()

    if not situacao_inicial:
        return JsonResponse(
            ResponsePattern.error('mailing', ['Situação INICIAL não configurada para esta carteira.']),
            status=400
        )

    # Descobre próxima prioridade
    ultima_prioridade = (
            CampanhaCliente.objects
            .filter(campanha=campanha)
            .order_by('-prioridade')
            .values_list('prioridade', flat=True)
            .first()
        ) or 0

    obj, created = CampanhaCliente.objects.get_or_create(
        campanha=campanha,
        cliente=cliente,
        defaults={
            'situacao': situacao_inicial,
            'prioridade': ultima_prioridade + 1,
        }
    )

    if not created:
        return JsonResponse(
            ResponsePattern.error('mailing', ['Cliente já está no mailing desta campanha.']),
            status=400
        )

    return JsonResponse(
        ResponsePattern.success('mailing', ['✓ Cliente adicionado ao mailing!']), status=200
    )


@login_required
@require_POST
def importar_csv_mailing(request, campanha_id):
    """
    Importa uma lista de clientes (via CSV parseado no front) para o mailing.
    Body esperado: { "clientes": [ {"documento": "..."}, ... ] }
    """
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)

    try:
        data = json.loads(request.body)
        clientes = data.get('clientes', [])
    except json.JSONDecodeError:
        return JsonResponse(ResponsePattern.error('mailing', ['JSON inválido']), status=400)

    if not clientes:
        return JsonResponse(
            ResponsePattern.error('mailing', ['Nenhum cliente para importar.']), status=400
        )

    situacao_inicial = campanha.carteira.situacoes.filter(
        tipo='INICIAL'
    ).first()

    if not situacao_inicial:
        return JsonResponse(
            ResponsePattern.error('mailing', ['Situação INICIAL não configurada para esta carteira.']),
            status=400
        )

    # Prioridade base
    ultima_prioridade = (
        CampanhaCliente.objects
        .filter(campanha=campanha)
        .order_by('-prioridade')
        .values_list('prioridade', flat=True)
        .first()
    ) or 0

    documentos = [str(c.get('documento', '')).strip() for c in clientes if c.get('documento')]
    prioridade_map = {}
    for i, c in enumerate(clientes):
        doc = str(c.get('documento', '')).strip()
        pri = c.get('prioridade', ultima_prioridade + i + 1)
        try:
            prioridade_map[doc] = int(pri)
        except (ValueError, TypeError):
            prioridade_map[doc] = ultima_prioridade + i + 1

    clientes_qs = Cliente.objects.filter(
        empresa=request.empresa,
        documento__in=documentos
    )

    # IDs já no mailing
    ja_no_mailing = set(
        CampanhaCliente.objects
        .filter(campanha=campanha, cliente__in=clientes_qs)
        .values_list('cliente_id', flat=True)
    )

    novos = []
    for cliente in clientes_qs:
        if cliente.id in ja_no_mailing:
            continue
        novos.append(CampanhaCliente(
            campanha=campanha,
            cliente=cliente,
            situacao=situacao_inicial,
            prioridade=prioridade_map.get(cliente.documento, ultima_prioridade + 1),
        ))

    CampanhaCliente.objects.bulk_create(novos, ignore_conflicts=True)

    nao_encontrados = len(documentos) - clientes_qs.count()
    duplicados = len(ja_no_mailing)
    importados = len(novos)

    partes = [f'✓ {importados} cliente(s) importado(s).']
    if duplicados:
        partes.append(f'{duplicados} já estavam no mailing.')
    if nao_encontrados:
        partes.append(f'{nao_encontrados} documento(s) não encontrado(s) no sistema.')

    return JsonResponse(
        ResponsePattern.success('mailing', [' '.join(partes)]), status=200
    )


@login_required
@require_GET
def resumo_mailing(request, campanha_id):
    """Retorna contagem de clientes por situação na campanha."""
    campanha = get_object_or_404(Campanha, pk=campanha_id, empresa=request.empresa)

    qs = CampanhaCliente.objects.filter(campanha=campanha)

    total = qs.count()

    def contar(tipo):
        return qs.filter(situacao__tipo=tipo).count()

    return JsonResponse({
        'total': total,
        'inicial': contar('INICIAL'),
        'curso': contar('CURSO'),
        'agenda': contar('AGENDA'),
        'sucesso': contar('SUCESSO'),
        'insucesso': contar('INSUCESSO'),
        'outro': qs.filter(
            situacao__tipo__in=['SEMCONTATO', 'OUTRO', 'INSUCESSO']
        ).count(),
    })