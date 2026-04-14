from django.urls import path
from .views import relatorios

app_name = 'relatorios'

urlpatterns = [
    path('relatorio_vendas/', relatorios.relatorio_vendas, name='relatorio_vendas'),
    path('<int:venda_id>/', relatorios.detalhe_venda, name='detalhe_venda'),
    path('agendas_list/', relatorios.agendas_list, name='lista_agendas'),
    path("acionamentos/<int:agenda_id>/", relatorios.acionamentos_agenda, name="acionamentos_agenda"),
]