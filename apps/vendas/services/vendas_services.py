from decimal import Decimal
from apps.vendas.models import Venda, Parceiro, Produto, Oferta, Esteira, HistVenda
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.clientes.models import Cliente
from apps.agenda.models import Agenda
from apps.core.responses.pattern import ResponsePattern


class VendasService:
    @staticmethod
    def get_complements(usuario, cliente_id, id_agenda, empresa):
        cliente = Cliente.objects.filter(pk=cliente_id, empresa=empresa).first()
        if not cliente:
            return {
                "success": False,
                "messages": {
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
                "messages": {
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
                "messages": {
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
                "messages": {
                    "vendas": {"__all__": [f"{str(e)}"]}
                }
            }
        except IntegrityError as e:
            return {
                "success": False,
                "status": 400,
                "messages": {
                    "vendas": {"__all__": [f"Venda duplicada detectada."]}
                }
            }


    """ =============== Relatorio de esteiras =============== """
    @staticmethod
    def valores_e_formatos(data):
        contrato = data.get('contrato', '').strip()
        if not contrato:
            messages = ['Contrato não pode ser vazio.']
            return ResponsePattern.error('contrato', messages, status=400)

        # Converte para Decimal (evita o erro "max 2 decimal places" do full_clean)
        campos_decimal = ['valor', 'parcela', 'taxa']
        for campo in campos_decimal:
            data[campo] = Decimal(str(data.get(campo, ''))).quantize(Decimal('0.01'))
            if data[campo] <= 0:
                messages = [f'{campo.capitalize()} não pode ser menor que 1.']
                return ResponsePattern.error(campo, messages)

        return ResponsePattern.success_data(data)

    @staticmethod
    def atualiza_oferta_prazo(venda, user, oferta, prazo, alteracoes):
        prazo = int(prazo)
        if prazo < oferta.prazo_min or prazo > oferta.prazo_max:
            messages = ['Prazo menos que o permitido para oferta.']
            return ResponsePattern.error('oferta', messages)

        try:
            with transaction.atomic():

                venda.oferta = oferta
                venda.produto_nome = oferta.produto.nome
                venda.parceiro_nome = oferta.parceiro.nome
                venda.comissao = oferta.comissao
                venda.prazo = prazo
                venda.save(update_fields=[
                    'oferta', 'prazo', 'produto_nome', 'parceiro_nome', 'comissao'
                ])

                VendasService.adiciona_comentario(venda, user, alteracoes)
            return ResponsePattern.success('oferta', ['✓ Oferta Atualiada com sucesso!'])
        except Exception as e:
            return ResponsePattern.error('oferta', [str(e)])

    @staticmethod
    def update_valores(venda, dados, user, changes):
        """
        Regra de update do model
        """
        try:
            with transaction.atomic():
                venda.contrato = dados['contrato']
                venda.valor = dados['valor']
                venda.parcela = dados['parcela']
                venda.taxa = dados['taxa']
                venda.full_clean()
                venda.save()

                VendasService.adiciona_comentario(venda, user, changes)

            messages = ["✓ Valores atualizados com sucesso."]
            return ResponsePattern.success('venda', messages)

        except ValidationError as e:
            return ResponsePattern.error("venda", e.message_dict)
        except Exception as e:
            return ResponsePattern.error("venda", e)

    @staticmethod
    def update_agente_venda(venda, responsavel, user, alteracoes):
        try:
            with transaction.atomic():
                venda.usuario = responsavel
                venda.carteira_nome = responsavel.agente.carteira.nome
                venda.equipe_nome = responsavel.agente.equipe.nome
                venda.save(update_fields=['usuario', 'carteira_nome', 'equipe_nome'])

                VendasService.adiciona_comentario(venda, user, alteracoes)

            return ResponsePattern.success('agente', ['✓ Agente alterado com sucesso.'])
        except Exception as e:
            return ResponsePattern.error('agente', [f'{str(e)}'])

    @staticmethod
    def update_esteira(venda, user, esteira, comentario):
        try:
            with transaction.atomic():
                venda.esteira = esteira
                venda.save(update_fields=['esteira'])

                VendasService.adiciona_comentario(venda, user, comentario)

            # Re-renderiza a timeline atualizada
            historico = venda.historico.order_by('-data').select_related('esteira', 'usuario')

            return ResponsePattern.success_data(historico)

        except ValidationError as e:
            return ResponsePattern.error('esteira_hist', [str(e)])
        except Exception as e:
            return ResponsePattern.error('esteira_hist', [str(e)])

    @staticmethod
    def adiciona_comentario(venda, user, alteracoes):
        if isinstance(alteracoes, list):
            comentario = " | ".join(alteracoes)
        else:
            comentario = alteracoes

        HistVenda.objects.create(
            venda=venda,
            esteira=venda.esteira,
            usuario=user,
            comentario=f'{comentario} por {user.get_full_name() or user.user.username}.'
        )


