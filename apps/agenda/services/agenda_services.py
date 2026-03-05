from apps.agenda.models import Agenda, Acionamento, Situacao
from apps.clientes.models import Cliente
from django.db import transaction
from django.utils import timezone

class AgendamentoService:

    def criar_ou_atualizar(self, cliente_id, usuario):
        cliente = Cliente.objects.get(pk=cliente_id)
        usuario = usuario
        carteira = usuario.agente.carteira
        equipe = usuario.agente.equipe
        perfil = usuario.agente.perfil

        with transaction.atomic():

            agenda = (
                Agenda.objects
                .select_for_update()
                .filter(
                    cliente=cliente,
                    carteira=carteira,
                    agenda_ativa=True
                )
                .first()
            )

            situacao_atendimento = Situacao.objects.filter(
                nome="Atendimento"
            ).first()

            # 🔹 Caso 1: Existe agenda ativa
            if agenda:

                # Mesmo usuário → retoma
                if agenda.usuario == usuario:
                    agenda.situacao = situacao_atendimento
                    agenda.save()

                    # Atualiza ou cria acionamento
                    self._criar_ou_atualizar_acionamento(agenda)

                    return {
                        "success": True,
                        "message": "Retomando Atendimento!",
                        "agenda": agenda
                    }

                # Outro usuário da mesma carteira
                else:
                    return {
                        "success": False,
                        "message": "Cliente já está em atendimento por outro agente."
                    }

            # 🔹 Caso 2: Não existe agenda ativa → cria nova
            nova_agenda = Agenda.objects.create(
                cliente=cliente,
                usuario=usuario,
                carteira=carteira,
                equipe=equipe,
                perfil=perfil,
                modo="Ativo",
                canal="Campanha da sorte",
                situacao=situacao_atendimento
            )

            # Cria acionamento para a nova agenda
            self._criar_ou_atualizar_acionamento(nova_agenda)

            return {
                "success": True,
                "message": "Novo atendimento iniciado!",
                "agenda": nova_agenda
            }

    def _criar_ou_atualizar_acionamento(self, agenda):
        """
        Atualiza ou cria um acionamento para a agenda.
        """
        acionamento = Acionamento.objects.get(
            agenda=agenda,
            data_finalizado__isnull=True
        )

        if acionamento:
            # Atualiza a situação e mantém data_acionamento original
            acionamento.situacao = agenda.situacao
            acionamento.save()
        else:
            # Cria novo acionamento
            Acionamento.objects.create(
                agenda=agenda,
                situacao=agenda.situacao
            )

    def registrar_situacao(self, id_agenda, situacao, dataAgenda, telefone, comentario):
        try:
            with transaction.atomic():
                agenda = Agenda.objects.filter(pk=id_agenda, agenda_ativa=True).first()
                if not agenda:
                    return {
                        "success": False,
                        "messages": {
                            "agenda": {"warning": ["Agenda não encontrada ou já finalizada"]}
                        }
                    }
                acionamento = Acionamento.objects.get(
                    agenda=agenda,
                    data_finalizado__isnull=True
                )
                if not acionamento:
                    return {
                        "success": False,
                        "messages": {
                            "agenda": {"warning": ["Agenda não encontrada ou já finalizada"]}
                        }
                    }

                sit = Situacao.objects.get(pk=situacao)

                if sit.tipo == "AGENDA":
                    agenda.data_hora_retorno = dataAgenda
                else:
                    agenda.data_finalizado = timezone.now()

                agenda.situacao = sit
                agenda.telefone = telefone
                agenda.save()

                acionamento.situacao = sit
                acionamento.data_finalizado = timezone.now()
                acionamento.comentario = comentario
                acionamento.save()
            return {
                "success": True,
                "messages": {
                    "agenda": {"success": ["Situacao registrada com sucesso!"]}
                }
            }
        except Exception as e:
            return {
                    "success": False,
                    "messages": {
                        "agenda": {"error": ["Algo deu errado", f"{e}"]}
                    }
                }

