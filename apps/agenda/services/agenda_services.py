from apps.agenda.models import Agenda, Acionamento, Situacao
from apps.clientes.models import Cliente
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

class AgendamentoService:

    def criar_ou_atualizar(self, cliente_id, usuario):
        cliente = get_object_or_404(
            Cliente.objects.select_related('empresa'),
            pk=cliente_id,
            empresa=usuario.agente.carteira.empresa
        )
        carteira = usuario.agente.carteira
        equipe = usuario.agente.equipe
        perfil = usuario.agente.perfil

        try:
            with transaction.atomic():

                agenda = (
                    Agenda.objects
                    .select_for_update()
                    .select_related('situacao', 'usuario', 'carteira')
                    .filter(
                        cliente=cliente,
                        carteira=carteira,
                        agenda_ativa=True
                    )
                    .first()
                )

                situacao_atendimento = Situacao.objects.filter(
                    tipo="CURSO", carteira=carteira
                ).first()

                if not situacao_atendimento:
                    return {
                        "success": False,
                        "errors": "Nenhuma situação de atendimento configurada para esta carteira."
                    }

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
                            "errors": f"Cliente agendado com outro agente"
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
        except Exception as e:
            return {
                "success": False,
                "errors": f"{str(e)}"
            }

    def _criar_ou_atualizar_acionamento(self, agenda):
        """
        Atualiza ou cria um acionamento para a agenda.
        """
        acionamento = (Acionamento.objects
            .select_related('agenda', 'situacao')
            .filter(agenda=agenda, data_finalizado__isnull=True
            ).first()
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

    def registrar_situacao(self, id_agenda, situacao, dataAgenda, telefone, comentario, usuario):
        from apps.core.validacoes import Validar
        if not Validar().valida_Fone(telefone):
            return {
                "success": False,
                "errors": {
                    "agenda": {"warning": ["Telefone Não pode ser vazio, e deve conter apenas números!"]}
                }
            }

        try:
            with transaction.atomic():
                agenda = (
                    Agenda.objects
                    .select_for_update()
                    .select_related('situacao', 'usuario')
                    .filter(
                        pk=id_agenda,
                        agenda_ativa=True,
                        carteira__empresa=usuario.agente.carteira.empresa
                    )
                    .first()
                )

                if not agenda:
                    return {
                        "success": False,
                        "errors": {
                            "agenda": {"warning": ["Agenda não encontrada ou já finalizada"]}
                        }
                    }
                acionamento = Acionamento.objects.select_related('agenda').filter(
                    agenda=agenda,
                    data_finalizado__isnull=True
                ).first()
                if not acionamento:
                    return {
                        "success": False,
                        "errors": {
                            "agenda": {"warning": ["Agenda não encontrada ou já finalizada"]}
                        }
                    }

                # ← verifica se o usuário é o dono da agenda
                if agenda.usuario != usuario:
                    return {
                        "success": False,
                        "errors": {
                            "agenda": {"warning": ["Você não tem permissão para registrar nesta agenda"]}
                        }
                    }

                sit = Situacao.objects.get(pk=situacao)

                if sit.tipo == "AGENDA":
                    if dataAgenda == "":
                        return {
                            "success": False,
                            "errors": {
                                "agenda": {"__all__": ["Data não pode ser vazio para Agendamento"]}
                            }
                        }

                    if comentario.strip() == "":
                        return {
                            "success": False,
                            "errors": {
                                "agenda": {"warning": ["Comentário não pode ser vazio"]}
                            }
                        }

                    agenda.data_hora_retorno = parse_datetime(dataAgenda)
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
        except ValidationError as e:
            return {
                "success": False,
                "errors": e.message_dict  # já vem formatado por campo
            }
        except Exception as e:
            return {
                "success": False,
                "errors": {
                    "agenda": {"__all__": ["Algo deu errado", f"{str(e)}"]}
                }
            }