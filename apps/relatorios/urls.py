from django.urls import path
from .views import relatorios

app_name = 'relatorios'

urlpatterns = [
    path('relatorio_vendas/', relatorios.relatorio_vendas, name='relatorio_vendas'),
    path('detalhe/<int:id>/', relatorios.detalhe_venda, name='detalhe_venda'),
]