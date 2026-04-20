from django.urls import path
from apps.usuarios.views import agentes, configuracoes

app_name = 'usuarios'

urlpatterns = [
    path('agentes/', agentes.lista_agentes, name='lista_agentes'),
    path('novo_agente/', agentes.novo_agente, name='novo_agente'),
    path('agente/<int:agente_id>/toggle/', agentes.toggle_ativo_agente, name='toggle_agente'),
    path('agente/<int:agente_id>/editar/', agentes.editar_agente, name='editar_agente'),

    # ── Configurações: Perfis e Equipes ──
    path('configuracoes/', configuracoes.lista_configuracoes, name='lista_configuracoes'),

    # Perfis
    path('perfil/', configuracoes.perfil_detail, name='perfil_criar'),
    path('perfil/<int:perfil_id>/', configuracoes.perfil_detail, name='perfil_detalhe'),
    path('perfil/<int:perfil_id>/toggle/', configuracoes.perfil_toggle, name='perfil_toggle'),

    # Equipes
    path('equipe/', configuracoes.equipe_detail, name='equipe_criar'),
    path('equipe/<int:equipe_id>/', configuracoes.equipe_detail, name='equipe_detalhe'),
    path('equipe/<int:equipe_id>/toggle/', configuracoes.equipe_toggle, name='equipe_toggle'),
]