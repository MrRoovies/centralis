from apps.vendas.models import Venda, Esteira, Produto, Parceiro
from apps.usuarios.models import Carteira
from django.contrib.auth.models import User
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from apps.core.regras_acesso import RegrasAcesso



class RelatorioVendasService:
    def gerar(self, empresa, filtro, usuario):
        qs = listar_vendas(empresa, filtro, usuario)

        return qs.select_related(
            'cliente',
            'oferta__produto',
            'oferta__parceiro',
            'esteira',
            'usuario'
        ).order_by('-created_at')

    def get_context_relatorio(self, empresa, vendas, filtro, totais):
        return {
            "vendas": vendas,
            "carteiras": Carteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "esteiras": Esteira.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "produtos": Produto.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "parceiros": Parceiro.objects.filter(empresa=empresa, ativo=True).order_by('nome'),
            "usuarios": User.objects.filter(agente__carteira__empresa=empresa).order_by('first_name'),
            'filtros': filtro,
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

def listar_vendas(empresa, filtro, usuario):
    qs = Venda.objects.filter(
        empresa=empresa
    )
    qs = RegrasAcesso(usuario).model_filter(qs)
    qs = qs.filter(**filtro)
    return qs
