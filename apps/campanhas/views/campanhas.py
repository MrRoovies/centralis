from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

from apps.campanhas.models import Campanha, CampanhaCliente
from apps.campanhas.services.campanha_services import CampanhaService
from apps.clientes.models import Cliente, Email, Telefone, Endereco
from apps.agenda.models import Situacao
from apps.agenda.services.agenda_services import AgendamentoService
from apps.vendas.forms import VendaForm


@login_required
@require_GET
def painel_campanhas(request):
    """Lista as Campanhas que o agente está cadastrado"""

    from apps.campanhas.models import CampanhaAgente
    usuario = request.user
    campanhas = (CampanhaAgente.objects
        .select_related('campanha', 'campanha__carteira')
        .filter(
            agente=usuario.agente,
            campanha__distribuicao_ativa=True,
            campanha__empresa=request.empresa,
            campanha__carteira=usuario.agente.carteira,
        )
    )
    context = {"campanhas_agente": campanhas}
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

    situacoes = Situacao.objects.filter(carteira=usuario.agente.carteira)
    situacoes_tela = situacoes.filter(ativo=True)

    if proximo.situacao.tipo != "CURSO":
        # Criar ou retomar agenda
        resultado = AgendamentoService().criar_ou_atualizar(
            proximo.cliente.id,
            usuario,
            modo="Campanha Manual",
            canal=campanha.nome
        )

        if not resultado["success"]:
            return JsonResponse({"fim_da_fila": False, "erro": resultado["errors"]}, status=400)

        situacao_curso = situacoes.filter(tipo="CURSO").first()

        proximo.agente_responsavel = usuario
        proximo.agenda = resultado["agenda"]
        proximo.situacao = situacao_curso
        proximo.save()
    else:
        resultado = {
            "success": True,
            "agenda": proximo.agenda,
            "message": "Retomando atendimento"
        }

    # Carregar cliente com prefetch para o template
    cliente = get_object_or_404(
        Cliente.objects
        .prefetch_related(
            Prefetch('emails',    queryset=Email.objects.filter(ativo=True)),
            Prefetch('telefones', queryset=Telefone.objects.filter(ativo=True)),
            Prefetch('enderecos', queryset=Endereco.objects.filter(ativo=True)),
        ),
        pk=proximo.cliente.id,
        empresa=request.empresa,
    )
    restantes = CampanhaService.restantes_mailing(campanha)

    html = render_to_string(
        "clientes/partials/card_atendimento_cliente.html",
        {
            "cliente":     cliente,
            "situacoes":   situacoes_tela,
            "nova_agenda": resultado,
            "venda_form":  VendaForm(prefix="venda", empresa=request.empresa),
        },
        request=request,
    )

    return JsonResponse({
        "fim_da_fila": False,
        "html":        html,
        "restantes":   restantes,
    })