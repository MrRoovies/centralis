from apps.agenda.models import Agenda, Acionamento, Situacao
from apps.clientes.models import Cliente
from django.db import transaction

class Agendamento_service:

    def __init__(self, cliente_id, usuario):
        self.cliente = Cliente.objects.get(pk=cliente_id)
        self.usuario = usuario
        self.carteira = usuario.agente.carteira
        self.equipe = usuario.agente.equipe
        self.perfil = usuario.agente.perfil

    def executar(self):

        with transaction.atomic():

            agenda = (
                Agenda.objects
                .select_for_update()
                .filter(
                    cliente=self.cliente,
                    carteira=self.carteira,
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
                if agenda.usuario == self.usuario:
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
                cliente=self.cliente,
                usuario=self.usuario,
                carteira=self.carteira,
                equipe=self.equipe,
                perfil=self.perfil,
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
        acionamento = Acionamento.objects.filter(
            agenda=agenda,
            data_finalizado__isnull=True
        ).first()

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


