from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, F
from itertools import groupby

from apps.campanhas.models import Campanha, CampanhaCliente, CampanhaAgente
from apps.campanhas.services.campanha_services import CampanhaService
from apps.clientes.services.cliente_service import ClienteService

from apps.clientes.models import Cliente, Email, Telefone, Endereco, DadosBancarios
from apps.agenda.models import Situacao
from apps.agenda.services.agenda_services import AgendamentoService
from apps.vendas.forms import VendaForm
import json


@login_required
@require_GET
def painel_campanhas(request):
    """Lista as Campanhas que o agente está cadastrado"""


    usuario = request.user
    campanhas = (CampanhaAgente.objects
        .select_related('campanha', 'campanha__carteira')
        .filter(
            agente=usuario.agente,
            campanha__distribuicao_ativa=True,
            campanha__empresa=request.empresa,
            campanha__carteira=usuario.agente.carteira,
        ).order_by('campanha__modo_atendimento')
    )

    campanhas_por_tipo = {
        tipo: list(items)
        for tipo, items in groupby(
            campanhas,
            key=lambda x: x.campanha.modo_atendimento
        )
    }
    context = {"campanhas_por_tipo": campanhas_por_tipo}
    return render(request, "campanhas/campanhas.html", context)


@login_required
@require_GET
def atender(request, id_campanha):
    """Renderiza a tela de atendimento da campanha selecionada."""

    campanha = get_object_or_404(
        Campanha,
        id=id_campanha,
        empresa=request.empresa,
        carteira=request.user.agente.carteira,
        distribuicao_ativa=True,
    )
    nao_tabulado = CampanhaService.nao_tabulado(campanha, request.user)
    agendados = CampanhaService.agendados(campanha, request.user)
    restantes = CampanhaService.restantes_mailing(campanha)

    context = {
        "campanha": campanha,
        "restantes": restantes,
        "nao_tabulado": nao_tabulado,
        "agendados": agendados
    }
    return render(request, "campanhas/atendimento_campanha.html", context)


@login_required
@require_GET
def proximo_cliente(request, id_campanha):
    """
    Retorna o HTML do card do próximo cliente da fila.

    Fluxo:
    1. Busca o próximo CampanhaCliente pendente (ordenado por prioridade).
    2. Chama AgendamentoService para criar/retomar a agenda.
    3. Renderiza o partial 'clientes/partials/card_atendimento_cliente.html'
       (o mesmo layout de atendimento_cliente.html) e devolve como JSON.
    """
    service = CampanhaService
    usuario = request.user
    campanha = get_object_or_404(
        Campanha,
        id=id_campanha,
        empresa=request.empresa,
        carteira=usuario.agente.carteira,
    )

    # Próximo cliente: não finalizado, ordenado por prioridade
    proximo = service.proximo_cliente_para_atendimento(campanha, usuario)

    if not proximo:
        return JsonResponse({"fim_da_fila": True})

    situacoes = campanha.carteira.situacoes.all()
    situacoes_tela = situacoes.filter(ativo=True)

    if proximo.situacao.tipo != "CURSO":
        # Criar ou retomar agenda
        resultado = AgendamentoService().criar_ou_atualizar(
            proximo.cliente.id,
            usuario,
            modo=campanha.modo_atendimento,
            canal=campanha.nome
        )

        if not resultado["success"]:
            if resultado["messages"]['agenda']['warning'] == ["Cliente agendado com outro agente"]:
                situacao_outro = situacoes.filter(tipo="OUTRO").first()
                proximo.situacao = situacao_outro
            return JsonResponse({"fim_da_fila": False, "messages": resultado["messages"]}, status=400)

        situacao_curso = situacoes.filter(tipo="CURSO").first()
        proximo.agente_responsavel = usuario
        proximo.agenda = resultado["agenda"]
        proximo.tentativas = F('tentativas') + 1
        proximo.situacao = situacao_curso
        proximo.save()
    else:
        resultado = {
            "success": True,
            "agenda": proximo.agenda,
            "messages": {
                "agenda" : { "success": ["Retomando Atendimento"] }
            }
        }

    # Carregar cliente com prefetch para o template
    cliente = get_object_or_404(
        Cliente.objects
        .prefetch_related(
            Prefetch('emails',    queryset=Email.objects.filter(ativo=True)),
            Prefetch('telefones', queryset=Telefone.objects.filter(ativo=True)),
            Prefetch('enderecos', queryset=Endereco.objects.filter(ativo=True)),
            Prefetch('dados_bancarios', queryset=DadosBancarios.objects.select_related('banco').filter()
            ),
        ),
        pk=proximo.cliente.id,
        empresa=request.empresa,
    )
    restantes = CampanhaService.restantes_mailing(campanha)
    whats_app_message = service.mensagemWhats_app(campanha, cliente)

    html = render_to_string(
        "clientes/partials/card_atendimento_cliente.html",
        {
            "cliente":     cliente,
            "situacoes":   situacoes_tela,
            "nova_agenda": resultado,
            "whats_app_message": whats_app_message,
            "venda_form":  VendaForm(prefix="venda", empresa=request.empresa),
        },
        request=request,
    )

    return JsonResponse({
        "fim_da_fila": False,
        "html": html,
        "restantes": restantes,
        "messages": resultado["messages"]
    })


@login_required
@require_GET
def adiantar_agenda(request, id_campanha):
    usuario = request.user

    campanha_cliente = get_object_or_404(
        CampanhaCliente,
        pk=id_campanha,
        agente_responsavel=usuario,
        situacao__tipo="AGENDA"
    )

    resultado = AgendamentoService().criar_ou_atualizar(
        campanha_cliente.cliente.id,
        usuario,
        modo=campanha_cliente.campanha.modo_atendimento,
        canal=campanha_cliente.campanha.nome
    )

    if not resultado["success"]:
        return JsonResponse({"erro": resultado["errors"]}, status=400)

    situacoes = campanha_cliente.campanha.carteira.situacoes.all()
    situacoes_tela = situacoes.filter(ativo=True)

    situacao_curso = situacoes.filter(tipo="CURSO").first()

    campanha_cliente.situacao = situacao_curso
    campanha_cliente.tentativas = F('tentativas') + 1
    campanha_cliente.save()

    # Carregar cliente com prefetch para o template
    cliente = get_object_or_404(
        Cliente.objects
        .prefetch_related(
            Prefetch('emails', queryset=Email.objects.filter(ativo=True)),
            Prefetch('telefones', queryset=Telefone.objects.filter(ativo=True)),
            Prefetch('enderecos', queryset=Endereco.objects.filter(ativo=True)),
        ),
        pk=campanha_cliente.cliente.id,
        empresa=request.empresa,
    )
    restantes = CampanhaService.restantes_mailing(campanha_cliente.campanha)

    html = render_to_string(
        "clientes/partials/card_atendimento_cliente.html",
        {
            "cliente": cliente,
            "situacoes": situacoes_tela,
            "nova_agenda": resultado,
            "venda_form": VendaForm(prefix="venda", empresa=request.empresa),
        },
        request=request,
    )

    return JsonResponse({
        "fim_da_fila": False,
        "html": html,
        "restantes": restantes,
        "messages": resultado["messages"]
    })


"""
Função será responsável por: 
incluir o cliente na campanha receptiva
Abrir a tela da campanha com o atendimento em aberto
"""
@login_required
@require_POST
def atender_receptivo(request):
    if not request.body:
        return JsonResponse({
            "success": False,
            "messages": {
                "campanha": { "error": ["Nenhum dado recebido"]}
                }
            }
        )
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "messages": {
                "campanha": {"error": ["JSON inválido"]}
            }
        }, status=400)

    cliente_id = data.get('cliente_id')
    canal = data.get('canal')

    if not cliente_id or not canal:
        return JsonResponse({
            "success": False,
            "messages": {
                "campanha": {"error": ["Dados obrigatórios não enviados"]}
            }
        }, status=400)

    usuario = request.user

    """Buscar campanha receptiva para inserção do cliente"""
    campanha_receptiva = (CampanhaAgente.objects
        .select_related('campanha', 'campanha__carteira')
        .filter(
           agente=usuario.agente,
           campanha__distribuicao_ativa=True,
           campanha__empresa=request.empresa,
           campanha__carteira=usuario.agente.carteira,
           campanha__modo_atendimento="RECEPTIVO"
        ).first())

    if not campanha_receptiva:
        return JsonResponse({
            "success": False,
            "messages": {
                "campanha": { "warning": ["Campanha Receptiva não localizada"]}
                }
            }, status=404)

    cliente = ClienteService.buscar_por_id(request.empresa, data['cliente_id'])

    # Criar ou retomar agenda
    resultado = AgendamentoService().criar_ou_atualizar(
        cliente.id,
        usuario,
        modo=campanha_receptiva.campanha.modo_atendimento,
        canal=data['canal']
    )

    if not resultado["success"]:
        return JsonResponse({"fim_da_fila": False, "messages": resultado["messages"]}, status=400)

    situacao_curso = Situacao.objects.filter(
        carteira=usuario.agente.carteira,
        tipo="CURSO"
    ).first()

    try:
        obj, created = CampanhaCliente.objects.get_or_create(
            campanha=campanha_receptiva.campanha, cliente=cliente,
            defaults={
                'agente_responsavel': usuario,
                'situacao': situacao_curso,
                'agenda': resultado["agenda"],
                'prioridade': 1,
                'tentativas': 1
            }
        )
        if not created:
            update_data = {
                "agente_responsavel": usuario,
                "situacao": situacao_curso,
                "agenda": resultado["agenda"],
                "prioridade": 1,
            }
            for field, value in update_data.items():
                setattr(obj, field, value)

            obj.tentativas = F("tentativas") + 1
            obj.save(update_fields=[*update_data.keys(), "tentativas"])
            obj.refresh_from_db()

            mensagem = "Cliente localizado em receptivo"
        else:
            mensagem = "Cliente vinculado à campanha com sucesso"

        return JsonResponse({
            "success": True,
            "redirect_url": f"/campanhas/atender/{campanha_receptiva.campanha.id}",
            "messages": {
                "campanha": {"success": [mensagem]}
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "messages": {
                "campanha": {"success": [str(e)]}
            }
        }, status=500)