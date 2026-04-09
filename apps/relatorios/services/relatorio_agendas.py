from apps.agenda.models import Agenda, Acionamento, Situacao
from apps.usuarios.models import Carteira
from apps.campanhas.models import Campanha
from django.contrib.auth.models import User
from apps.core.regras_acesso import RegrasAcesso
from django.db.models import Count
from django.utils.dateparse import parse_date
from datetime import datetime, time
from django.utils import timezone



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
            "modos": [
                {"value": m[0], "label": m[1]}
                for m in Campanha.CHOICE_TIPOS
            ],
            "usuarios": User.objects.filter(agente__carteira__empresa=empresa).order_by('first_name'),
            'filtros': filtro,
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
    qs = qs.filter(**filtro)
    return qs