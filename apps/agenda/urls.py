from django.urls import path
from .views import agenda_cliente, situacoes

app_name = 'agenda'

urlpatterns = [
    path("historico/<int:cliente_id>/", agenda_cliente.hist_agenda_cliente, name="hist_agenda"),
    path("registrar", agenda_cliente.registrar_atendimento, name="registrar_atendimento"),

    path("situacoes", situacoes.situacoes_view, name="lista_situacoes"),

    # Drawer: criar (GET form vazio + POST criação)
    path('situacao/', situacoes.situacao_detail, name='situacao_nova'),

    # Drawer: editar (GET dados + POST atualização)
    path('situacao/<int:situacao_id>/', situacoes.situacao_detail, name='situacao_detail'),

    # Toggle ativo/inativo
    path('situacao/<int:situacao_id>/toggle/', situacoes.situacao_toggle, name='situacao_toggle'),
]