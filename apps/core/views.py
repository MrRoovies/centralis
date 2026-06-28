from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q

# Ajuste os imports conforme a estrutura do seu projeto
# Exemplos baseados nos padrões observados no código do projeto:

from apps.agenda.models import Agenda, Acionamento
from apps.vendas.models import Venda
from apps.campanhas.models import Campanha
from apps.usuarios.models import Agente
import datetime



# Create your views here.
def login_template(request):
    return render(request, "registration/login.html")

@require_http_methods(["POST"])
def login_view(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
            empresa=request.empresa
        )

        if user is None:
            return render(
                request,
                "registration/login.html",
                {"error": "Usuário ou senha incorretos"}
            )

        login(request, user)
        return redirect("/home")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Método inválido"}, status=400)


def erro_403(request, exception=None):
    return render(request, '403.html', status=403)


def erro_404(request, exception=None):
    return render(request, '404.html', status=404)


@login_required
def home(request):
    empresa = request.empresa
    hoje = timezone.localdate()
    ontem     = hoje - datetime.timedelta(days=1)
    inicio_mes = hoje.replace(day=1)
    inicio_mes_ant = (inicio_mes - datetime.timedelta(days=1)).replace(day=1)

    # ── KPIs ──────────────────────────────────────────────────
    try:
        agendamentos_hoje   = Agenda.objects.filter(carteira__empresa=empresa, data_hora_retorno__date=hoje).count()
        agendamentos_ontem  = Agenda.objects.filter(carteira__empresa=empresa, data_hora_retorno__date=ontem).count()
        agendamentos_delta  = agendamentos_hoje - agendamentos_ontem

        atendimentos_hoje = (
            Acionamento.objects.filter(
            data_acionamento__date=hoje, agenda__carteira__empresa=empresa
        ).count())

    except Exception as e:
        agendamentos_hoje  = 0
        agendamentos_delta = 0
        atendimentos_hoje  = 0

    try:
        vendas_mes     = Venda.objects.filter(empresa=empresa, created_at__gte=inicio_mes).count()
        vendas_mes_ant = Venda.objects.filter(empresa=empresa,
            created_at__gte=inicio_mes_ant, created_at__lt=inicio_mes
        ).count()
        vendas_delta   = vendas_mes - vendas_mes_ant

    except Exception:
        vendas_mes    = 0
        vendas_delta  = 0

    try:
        campanhas_ativas_qs = Campanha.objects.filter(empresa=empresa,
            distribuicao_ativa=True
        ).select_related('carteira').order_by('nome')

        campanhas_ativas_count = campanhas_ativas_qs.count()

    except Exception:
        campanhas_ativas_qs    = []
        campanhas_ativas_count = 0

    try:
        agentes_online = Agente.objects.filter(user__is_active=True).count()
    except Exception:
        agentes_online = 0

    kpi = {
        'agendamentos_hoje':  agendamentos_hoje,
        'agendamentos_delta': agendamentos_delta,
        'atendimentos_hoje':  atendimentos_hoje,
        'vendas_mes':         vendas_mes,
        'vendas_delta':       vendas_delta,
        'campanhas_ativas':   campanhas_ativas_count,
        'agentes_online':     agentes_online,
    }

    # ── Agendamentos do dia ───────────────────────────────────
    agendamentos_list = []
    try:
        qs = (
            Agenda.objects
            .filter(data_hora_retorno__date=hoje)
            .select_related('cliente', 'usuario', 'situacao')
            .order_by('data_hora_retorno')
            [:20]
        )

        SITUACAO_SLUG = {
            'INICIAL':    'inicial',
            'EM_CURSO':   'curso',
            'AGENDADO':   'agenda',
            'SUCESSO':    'sucesso',
            'INSUCESSO':  'insucesso',
        }

        for a in qs:
            agente_nome = '—'
            try:
                agente_nome = a.usuario.get_full_name() or a.usuario.username
            except Exception:
                pass

            situacao_str  = str(a.situacao) if a.situacao else '—'
            situacao_slug = SITUACAO_SLUG.get(
                getattr(a.situacao, 'tipo', ''), 'inicial'
            )

            agendamentos_list.append({
                'cliente_id':    a.cliente.id,
                'cliente_nome':  a.cliente.nome,
                'agente_nome':   agente_nome,
                'canal':         getattr(a, 'canal', '—'),
                'retorno':       a.retorno,
                'situacao':      situacao_str,
                'situacao_slug': situacao_slug,
                'ativa':         a.ativa,
            })

    except Exception as e:
        print(e)
        pass

    # ── Últimas vendas ────────────────────────────────────────
    ultimas_vendas = []
    try:
        qs = (
            Venda.objects
            .select_related('cliente', 'oferta__produto', 'oferta__parceiro')
            .order_by('-created_at')
            [:10]
        )

        for v in qs:
            ultimas_vendas.append({
                'id':           v.id,
                'contrato':     v.contrato,
                'cliente_nome': v.cliente.nome,
                'produto':      v.oferta.produto.nome,
                'parceiro':     v.oferta.parceiro.nome,
                'valor':        v.valor,
                'data':         v.created_at,
            })

    except Exception as e:
        pass

    # ── Campanhas ativas ──────────────────────────────────────
    campanhas_list = []
    try:
        for c in campanhas_ativas_qs[:8]:
            total_fila = Campanha.objects.filter(
                
                distribuicao_ativa=True
            ).count()

            campanhas_list.append({
                'id':         c.id,
                'nome':       c.nome,
                'carteira':   c.carteira.nome if c.carteira else '—',
                'modo':       c.modo_atendimento,
                'total_fila': total_fila,
            })

    except Exception:
        pass

    # ── Ranking de agentes (vendas no mês) ────────────────────
    ranking_agentes = []
    try:
        qs = (
            Venda.objects
            .filter(created_at__gte=inicio_mes)
            .values('usuario_id__first_name', 'usuario_id__last_name', 'usuario_id')
            .annotate(vendas=Count('id'))
            .order_by('-vendas')
            [:7]
        )
        maximo = qs[0]['vendas'] if qs else 1

        for row in qs:
            nome = (
                f"{row['usuario_id__first_name']} {row['usuario_id__last_name']}".strip()
                or '—'
            )
            partes = nome.split()
            iniciais = (partes[0][0] + partes[-1][0]).upper() if len(partes) >= 2 else nome[:2].upper()

            ranking_agentes.append({
                'nome':    nome,
                'iniciais': iniciais,
                'vendas':  row['vendas'],
                'pct':     round(row['vendas'] / maximo * 100),
            })

    except Exception:
        pass

    # ── Contexto ──────────────────────────────────────────────
    context = {
        'hoje':              hoje.strftime('%d de %B de %Y'),
        'kpi':               kpi,
        'agendamentos_hoje': agendamentos_list,
        'ultimas_vendas':    ultimas_vendas,
        'campanhas_ativas':  campanhas_list,
        'ranking_agentes':   ranking_agentes,
    }

    return render(request, 'home.html', context)