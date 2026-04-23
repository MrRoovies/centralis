from .views import campanhas, campanhas_admin
from django.urls import path

app_name = 'campanhas'

urlpatterns = [
    path('', campanhas.painel_campanhas, name="painel_campanhas"),
    path('atender/<int:id_campanha>', campanhas.atender, name="atender"),
    path('proximo_cliente/<int:id_campanha>/', campanhas.proximo_cliente, name="proximo_cliente"),
    path('adiantar_agenda/<int:id_campanha>/', campanhas.adiantar_agenda, name="adiantar_agenda"),
    path('atender_receptivo/', campanhas.atender_receptivo, name="atender_receptivo"),

# ── Novas rotas: Admin de Campanhas ──
    path('admin/', campanhas_admin.lista_campanhas_admin, name='admin_campanhas'),
    path('admin/nova/', campanhas_admin.campanha_detail, name='campanha_criar'),
    path('admin/<int:campanha_id>/', campanhas_admin.campanha_detail, name='campanha_detalhe'),
    path('admin/<int:campanha_id>/toggle/', campanhas_admin.toggle_campanha, name='campanha_toggle'),

    # Agentes
    path('admin/<int:campanha_id>/agentes/', campanhas_admin.agentes_campanha, name='agentes_campanha'),
    path('admin/<int:campanha_id>/agentes/vincular/', campanhas_admin.vincular_agente, name='vincular_agente'),
    path('admin/<int:campanha_id>/agentes/<int:agente_id>/desvincular/', campanhas_admin.desvincular_agente,
         name='desvincular_agente'),

    # Mailing
    path('admin/<int:campanha_id>/mailing/adicionar/', campanhas_admin.adicionar_cliente_mailing,
         name='adicionar_cliente_mailing'),
    path('admin/<int:campanha_id>/mailing/importar/', campanhas_admin.importar_csv_mailing,
         name='importar_csv_mailing'),
    path('admin/<int:campanha_id>/mailing/resumo/', campanhas_admin.resumo_mailing, name='resumo_mailing'),
]
