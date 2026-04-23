from apps.campanhas.models import Campanha, CampanhaCliente
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from apps.core.responses.pattern import ResponsePattern
from apps.usuarios.models import Carteira


class CampanhaService:
    @staticmethod
    def nao_tabulado(campanha, usuario):
        # Retorna lista de clientes vinculados ao agente para controle e atendimento #
        return (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="CURSO",
            )
            .order_by('prioridade').first()
        )


    @staticmethod
    def agendados(campanha, usuario):
        # Retorna lista de clientes vinculados ao agente para controle e atendimento #
        return (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao', 'agenda')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="AGENDA"
            )
            .order_by('prioridade')
        )


    @staticmethod
    def restantes_mailing(campanha):
        return (CampanhaCliente.objects.filter(
            campanha=campanha,
            situacao__tipo="INICIAL",
        ).count())


    @staticmethod
    def proximo_cliente_para_atendimento(campanha, usuario):
        # 1 Verifica se existe cliente em andamento
        em_curso = (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="CURSO",
            ).first()
        )
        if em_curso:
            return em_curso

        agendado = (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(
                agente_responsavel=usuario,
                campanha=campanha,
                situacao__tipo="AGENDA",
            ).first()
        )
        if agendado:
            if agendado.agenda.data_hora_retorno < timezone.now():
                return agendado

        # 2 Verifica se existe cliente em Fila
        proximo = (
            CampanhaCliente.objects
            .select_related('cliente', 'situacao')
            .filter(campanha=campanha, situacao__tipo="INICIAL")
            .order_by('prioridade')
            .first()
        )

        return proximo


class CampanhasAdmin:

    @staticmethod
    def lista_campanhas(empresa, filtros):
        qs = (
            Campanha.objects
            .filter(empresa=empresa)
            .select_related('carteira')
            .annotate(
                total_agentes=Count('campanhaagente',
                filter=Q(campanhaagente__ativo=True),
                distinct=True),
                total_clientes=Count('campanhacliente',
                distinct=True),
            )
            .order_by('-created_at')
        )

        if filtros:
            qs = qs.filter(**filtros)
        return qs

    @staticmethod
    def get_campanha(campanha_id, empresa):
        if campanha_id:
            campanha = Campanha.objects.get(pk=campanha_id, empresa=empresa)
            return ResponsePattern.success_data(
                {'campanha': {
                    'nome': campanha.nome,
                    'carteira_id': campanha.carteira_id,
                    'modo_atendimento': campanha.modo_atendimento,
                    'metodo_distribuicao': campanha.metodo_distribuicao,
                    'distribuicao_ativa': campanha.distribuicao_ativa,
                }}
            )
        else:
            return ResponsePattern.success_data({'campanha': {}})

    @staticmethod
    def cria_ou_edita(carteira_id, campanha_id, nome, modo_atendimento, metodo_distribuicao, distribuicao_ativa, empresa):
        try:
            with transaction.atomic():
                carteira = Carteira.objects.get(pk=carteira_id, empresa=empresa, ativo=True)
                if campanha_id:
                    campanha = Campanha.objects.get(pk=campanha_id, empresa=empresa)
                    campanha.nome = nome
                    campanha.carteira = carteira
                    campanha.modo_atendimento = modo_atendimento
                    campanha.metodo_distribuicao = metodo_distribuicao
                    campanha.distribuicao_ativa = distribuicao_ativa
                    campanha.save()
                    msg = '✓ Campanha atualizada com sucesso!'
                else:
                    Campanha.objects.create(
                        empresa=empresa,
                        nome=nome,
                        carteira=carteira,
                        modo_atendimento=modo_atendimento,
                        metodo_distribuicao=metodo_distribuicao,
                        distribuicao_ativa=distribuicao_ativa,
                    )
                    msg = '✓ Campanha criada com sucesso!'

                return ResponsePattern.success('campanha', [msg])

        except Exception as e:
            return ResponsePattern.error('campanha', [str(e)])