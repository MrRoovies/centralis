from apps.vendas.models import Venda, Esteira, Produto, Parceiro
from apps.usuarios.models import Carteira
from django.contrib.auth.models import User
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.dateparse import parse_date
from datetime import datetime, time

class FiltroRelatorioVendas:
    def __init__(self, data):
        self.data_inicio = data.get("data_inicio")
        self.data_fim = data.get("data_fim")
        self.esteira_id = data.get("esteira")
        self.produto_id = data.get("produto")
        self.parceiro_id = data.get("parceiro")
        self.carteira_id = data.get("carteira")
        self.usuario_id = data.get("usuario")

class RelatorioVendasService:
    def gerar(self, empresa, filtro):
        qs = listar_vendas(empresa, filtro)

        return qs.select_related(
            'cliente',
            'oferta__produto',
            'oferta__parceiro',
            'esteira',
            'usuario'
        ).order_by('-created_at')

    def get_context_relatorio(self, empresa, vendas, totais, filtro):
        return {
            "vendas": vendas,
            "carteiras": Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "esteiras": Esteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "produtos": Produto.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "parceiros": Parceiro.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "usuarios": User.objects.filter(agente__carteira__empresa=empresa).order_by('first_name'),
            'filtros':{
                'data_inicio': filtro.data_inicio or '',
                'data_fim': filtro.data_fim or '',
                'carteira': filtro.carteira_id or '',
                'esteira': filtro.esteira_id or '',
                'produto': filtro.produto_id or '',
                'parceiro': filtro.parceiro_id or '',
                'usuario': filtro.usuario_id or ''
            },
            'totais': totais
        }

    def calcular_totais(self, vendas):
        agregados = vendas.aggregate(
            total_valor=Sum('valor'),
            total_comissao=Sum(
                ExpressionWrapper(
                    F('valor') * F('comissao') / 100,
                    output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )
        )
        total_valor = agregados['total_valor'] or 0
        total_comissao = agregados['total_comissao'] or 0
        total_vendas = vendas.count()

        # Anota comissão calculada para exibir na linha
        qs = vendas.annotate(
            comissao_calculada=ExpressionWrapper(
                F('valor') * F('comissao') / 100,
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        return {
            'total_valor': total_valor,
            'total_comissao': total_comissao,
            'total_vendas': total_vendas,
            'qs': qs}

def listar_vendas(empresa, filtro):
    qs = Venda.objects.filter(
        empresa=empresa
    )

    if filtro.data_inicio:
        dt = parse_date(filtro.data_inicio)
        if dt:
            inicio = datetime.combine(dt, time.min)
            qs = qs.filter(created_at__gte=inicio)

    if filtro.data_fim:
        dt = parse_date(filtro.data_fim)
        if dt:
            fim = datetime.combine(dt, time.max)
            qs = qs.filter(created_at__lte=fim)

    if filtro.carteira_id:
        qs = qs.filter(esteira__carteira_id=filtro.carteira_id)

    if filtro.esteira_id:
        qs = qs.filter(esteira_id=filtro.esteira_id)

    if filtro.produto_id:
        qs = qs.filter(oferta__produto_id=filtro.produto_id)

    if filtro.parceiro_id:
        qs = qs.filter(oferta__parceiro_id=filtro.parceiro_id)

    if filtro.usuario_id:
        qs = qs.filter(usuario_id=filtro.usuario_id)

    return qs
