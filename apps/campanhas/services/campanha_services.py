from apps.campanhas.models import Campanha, CampanhaCliente, TagMessageWp
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from apps.core.responses.pattern import ResponsePattern
from apps.usuarios.models import Carteira
from django.utils import timezone
from apps.agenda.models import Situacao, Acionamento, CarteiraSituacao
import re

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
    

    @staticmethod
    def _resolver_campo(obj, caminho):
        atual = obj
        for parte in caminho.split('__'):
            if atual is None:
                return ''
            attr = getattr(atual, parte, None)
            if hasattr(attr, 'all'):  # é um Manager (relacionamento reverso)
                try:
                    atual = attr.order_by('-referencia').first()
                except Exception:
                    atual = attr.first()
            else:
                atual = attr
        return atual if atual is not None else ''


    @staticmethod
    def mensagemWhats_app(campanha, cliente):
        tags = TagMessageWp.objects.select_related('content_type').all()
        instancias_cache = {}
        contexto = {}

        for tag_obj in tags:
            ct = tag_obj.content_type

            if ct not in instancias_cache:
                model_class = ct.model_class()
                if ct.model == 'cliente':
                    instancias_cache[ct] = cliente
                else:
                    try:
                        instancias_cache[ct] = model_class.objects.filter(cliente=cliente).first()
                    except Exception:
                        instancias_cache[ct] = None

            instancia = instancias_cache[ct]
            valor = CampanhaService._resolver_campo(instancia, tag_obj.campo) if instancia else ''
            contexto[tag_obj.tag] = str(valor) if valor is not None else ''

        mensagem = campanha.texto_whatsapp
        if mensagem:
            for tag, valor in contexto.items():
                mensagem = mensagem.replace(tag, valor)
        return mensagem


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
                    'texto_whatsapp': campanha.texto_whatsapp,
                }}
            )
        else:
            return ResponsePattern.success_data({'campanha': {}})

    @staticmethod
    def cria_ou_edita(carteira_id, campanha_id, nome, modo_atendimento, metodo_distribuicao, distribuicao_ativa, msg_whatsapp, empresa):
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
                    campanha.texto_whatsapp = msg_whatsapp
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


    @staticmethod
    def finalizar_agendamentos_campanha(campanha):
        """
        Ao desativar a campanha, tabula automaticamente todo cliente que
        estava com situação tipo AGENDA para "Agenda Finalizada",
        finalizando também a Agenda e o Acionamento em aberto.
        """
        situacao_finalizada = Situacao.objects.filter(
            carteirasituacao__carteira=campanha.carteira,
            nome__iexact="Agenda Finalizada",
            ativo=False
        ).first()

        if not situacao_finalizada:
            return ResponsePattern.error(
                'agendamentos',
                ['Situação "Agenda Finalizada" não está cadastrada/vinculada a esta carteira.']
            )

        agendamentos = (
            CampanhaCliente.objects
            .select_related('agenda')
            .filter(campanha=campanha, situacao__tipo="AGENDA")
        )

        agora = timezone.now()
        total = 0

        try:
            with transaction.atomic():
                for cc in agendamentos:
                    cc.situacao = situacao_finalizada
                    cc.ultima_tentativa = agora
                    cc.save(update_fields=['situacao', 'ultima_tentativa'])

                    agenda = cc.agenda
                    if agenda and agenda.agenda_ativa:
                        agenda.situacao = situacao_finalizada
                        agenda.agenda_ativa = False
                        agenda.data_finalizado = agora
                        agenda.save(update_fields=[
                            'situacao', 'agenda_ativa', 'data_finalizado'
                        ])

                        Acionamento.objects.filter(
                            agenda=agenda,
                            data_finalizado__isnull=True
                        ).update(
                            situacao=situacao_finalizada,
                            data_finalizado=agora
                        )

                    total += 1

            return ResponsePattern.success(
                'agendamentos',
                [f'{total} agendamento(s) finalizado(s) automaticamente.']
            )

        except Exception as e:
            return ResponsePattern.error('agendamentos', [str(e)])