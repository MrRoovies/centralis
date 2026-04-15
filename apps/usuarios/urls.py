from django.urls import path
from apps.usuarios.views import agentes

app_name = 'usuarios'

urlpatterns = [
    path('agentes/', agentes.lista_agentes, name='lista_agentes'),
    path('novo_agente/', agentes.novo_agente, name='novo_agente'),
    path('agente/<int:agente_id>/toggle/', agentes.toggle_ativo_agente, name='toggle_agente'),
]