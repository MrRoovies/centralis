from django.urls import path
from .views import relatorios

app_name = 'relatorios'

urlpatterns = [
    path('relatorio_vendas/', relatorios.relatorio_vendas, name='relatorio_vendas'),

    path('agendas_list/', relatorios.agendas_list, name='lista_agendas'),
    path("acionamentos/<int:agenda_id>/", relatorios.acionamentos_agenda, name="acionamentos_agenda"),

    # ── Edicao ──
    path('<int:venda_id>/valores/', relatorios.editar_valores, name='editar_valores'),
    path('<int:venda_id>/oferta/', relatorios.editar_oferta, name='editar_oferta'),
    path('<int:venda_id>/responsavel/', relatorios.responsavel, name='responsavel'),
    path('<int:venda_id>/comentario_e_esteira/', relatorios.comentario_e_esteira, name='comentario_e_esteira'),
]