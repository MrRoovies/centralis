from apps.agenda.models import Agenda, Acionamento, Situacao
from apps.usuarios.models import Carteira
from django.contrib.auth.models import User
from apps.core.regras_acesso import RegrasAcesso
from django.db.models import Count
from django.utils.dateparse import parse_date
from datetime import datetime, time
from django.utils import timezone


class FiltroRelatorioAgendas:
    def __init__(self, data):
        self.data_inicio = data.get('data_inicio')
        self.data_fim = data.get('data_fim')
        self.carteira_id = data.get('carteira')
        self.situacao_id = data.get('situacao')
        self.situacao_tipo = data.get('situacao_tipo')
        self.usuario_id = data.get('usuario')
        self.modo = data.get('modo')
        self.ativa = data.get('ativa')


class RelatorioAgendaService:
    def gerar(self, empresa, filtro, usuario):
        qs = listar_agendas(empresa, filtro, usuario)

        return qs.select_related(
            'cliente',
            'usuario',
            'situacao',
            'carteira',
            'perfil'
            ).order_by('-data_entrada')


    def get_context_relatorio(self, empresa, agendas, filtro, totais):
        return {
            'agendas': agendas,
            "carteiras": Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "situacoes": Situacao.objects.filter(
                carteira__empresa=empresa,
                ativo=True).values('tipo').order_by('tipo', 'nome').distinct(),
            "modos": (
                    Agenda.objects
                    .filter(cliente__empresa=empresa)
                    .values_list('modo', flat=True)
                    .distinct()
                    .order_by('modo')
                ),
            "usuarios": User.objects.filter(agente__carteira__empresa=empresa).order_by('first_name'),
            'filtros': {
                'data_inicio': filtro.data_inicio or '',
                'data_fim': filtro.data_fim or '',
                'carteira': filtro.carteira_id or '',
                'situacao': filtro.situacao_id or '',
                'situacao_tipo': filtro.situacao_tipo or '',
                'usuario': filtro.usuario_id or '',
                'modo': filtro.modo or '',
                'ativa': filtro.ativa or '',
            },
            'totais': totais
        }

    def calcular_totais(self, agenda):
        qs = agenda.annotate(total_acionamentos=Count('acionamento'))
        total_agendas = qs.count()
        total_ativas = qs.filter(agenda_ativa=True).count()
        total_finalizadas = qs.filter(agenda_ativa=False).count()
        return {
            'total_agendas': total_agendas,
            'total_ativas': total_ativas,
            'total_finalizadas': total_finalizadas,
            }


def listar_agendas(empresa, filtro, usuario):
    qs = Agenda.objects.filter(
        cliente__empresa=empresa
    )
    qs = RegrasAcesso(usuario).model_filter(qs)

    if filtro.data_inicio:
        dt = parse_date(filtro.data_inicio)
        if dt:
            inicio = timezone.make_aware(datetime.combine(dt, time.min))
            qs = qs.filter(data_entrada__gte=inicio)

    if filtro.data_fim:
        dt = parse_date(filtro.data_fim)
        if dt:
            fim = timezone.make_aware(datetime.combine(dt, time.max))
            qs = qs.filter(data_entrada__lte=fim)

    if filtro.carteira_id:
        qs = qs.filter(carteira_id=filtro.carteira_id)

    if filtro.situacao_id:
        qs = qs.filter(situacao_id=filtro.situacao_id)

    if filtro.situacao_tipo:
        qs = qs.filter(situacao__tipo=filtro.situacao_tipo)

    if filtro.usuario_id:
        qs = qs.filter(usuario_id=filtro.usuario_id)

    if filtro.modo:
        qs = qs.filter(modo=filtro.modo)

    if filtro.ativa == '1':
        qs = qs.filter(agenda_ativa=True)

    elif filtro.ativa == '0':
        qs = qs.filter(agenda_ativa=False)

    return qs