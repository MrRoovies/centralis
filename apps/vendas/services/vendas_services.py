from apps.vendas.forms import VendaForm
from apps.vendas.models import Venda, Parceiro, Produto, Oferta, Esteira, HistVenda
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.clientes.models import Cliente
from apps.agenda.models import Agenda


class VendasService:
    @staticmethod
    def get_complements(usuario, cliente_id, id_agenda, empresa):
        cliente = Cliente.objects.filter(pk=cliente_id, empresa=empresa).first()
        if not cliente:
            return {
                "success": False,
                "errors": {
                    "vendas": {"error": [f"Cliente não encontrado."]}
                }
            }

        esteira = Esteira.objects.filter(
            empresa=empresa,
            carteira=usuario.agente.carteira,
            tipo="INICIAL",
            ativo=True
        ).first()

        if not esteira:
            return{
                "success": False,
                "errors": {
                    "vendas": {"error": [f"Esteira INICIAL não cadastrada"]}
                }
            }

        agenda = Agenda.objects.filter(
            pk=id_agenda,
            cliente__empresa=empresa
        ).first()
        if not agenda:
            return {
                "success": False,
                "errors": {
                    "vendas": {"error": [f"Agenda não encontrada"]}
                }
            }

        return {
                "success": True,
                "data": {
                    "cliente": cliente,
                    "esteira": esteira,
                    "agenda": agenda,
                    "usuario": usuario
                }
            }

    @staticmethod
    def registrar_venda(venda_form, data, comentario):
        cliente = data["cliente"]
        agenda = data["agenda"]
        usuario = data["usuario"]
        esteira = data["esteira"]

        try:
            with transaction.atomic():
                novo = venda_form.save(commit=False)
                novo.cliente = cliente
                novo.agenda = agenda
                novo.carteira_nome = usuario.agente.carteira.nome
                novo.equipe_nome = usuario.agente.equipe.nome
                novo.empresa = usuario.agente.carteira.empresa
                novo.usuario = usuario
                novo.esteira = esteira
                novo.save()

                HistVenda.objects.create(
                    venda=novo,
                    esteira=esteira,
                    usuario=usuario,
                    comentario=comentario
                )

                return {
                    "success": True,
                    "status": 200,
                    "messages": {
                        "vendas": {"success": [f"Venda Registrada com sucesso!"]}
                    }
                }

        except ValidationError as e:
            return {
                "success": False,
                "status": 400,
                "errors": {
                    "vendas": {"__all__": [f"{str(e)}"]}
                }
            }
        except IntegrityError as e:
            return {
                "success": False,
                "status": 400,
                "errors": {
                    "vendas": {"__all__": [f"Venda duplicada detectada."]}
                }
            }