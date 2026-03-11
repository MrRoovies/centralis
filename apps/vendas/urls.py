from django.urls import path
from .views import contratos

app_name = 'vendas'

urlpatterns = [
    path('novo_contrato', contratos.registrar_venda, name='novo_contrato'),
    path('parceiros/', contratos.get_parceiros, name='get_parceiros'),
    path('produtos/', contratos.get_produtos, name='get_produtos'),
    path('ofertas/', contratos.get_ofertas, name='get_ofertas')
]