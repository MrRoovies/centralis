from apps.agenda.models import Agenda, Acionamento, Situacao, CarteiraSituacao
from apps.usuarios.models import Carteira
from django.contrib.auth.models import User
from apps.core.regras_acesso import RegrasAcesso
from django.db.models import Count
from datetime import datetime, time
from django.utils import timezone


class RelatorioAgendaService:
    def gerar(self, empresa, filtro, usuario):
        data_inicio = filtro.get("data_entrada__gte")
        data_fim = filtro.get("data_entrada__lte")

        if isinstance(data_inicio, str):
            data_inicio = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(data_inicio, "%Y-%m-%d").date(),
                    time.min
                )
            )

        if isinstance(data_fim, str):
            data_fim = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(data_fim, "%Y-%m-%d").date(),
                    time.max
                )
            )

        filtro["data_entrada__gte"] = data_inicio
        filtro["data_entrada__lte"] = data_fim

        qs = listar_agendas(empresa, filtro, usuario)

        return qs.select_related(
            'cliente',
            'usuario',
            'situacao',
            'carteira',
            'perfil'
            ).order_by('-data_entrada')


    def get_context_relatorio(self, empresa, agendas, filtro, totais):
        from apps.core.choices import ModoAtendimento
        return {
            'agendas': agendas,
            "carteiras": Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "situacoes": CarteiraSituacao.objects.filter(
                carteira__empresa=empresa,
                situacao__ativo=True).values('situacao__tipo').order_by('situacao__tipo').distinct(),
            "modos": [
                {"value": m[0], "label": m[1]}
                for m in ModoAtendimento.choices
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