from django.urls import path
from .views import cliente, email, telefone, endereco, importar, referencias

app_name = 'clientes'

urlpatterns = [
    path(r'search_cliente', cliente.search_cliente, name='search_cliente'),
    path('cliente_novo', cliente.cliente_novo, name='cliente_novo'),
    path('cliente/<int:id>', cliente.cliente, name='cliente'),
    path('cliente/<int:cliente_id>/edit', cliente.edita_cliente, name='edita_cliente'),

    path('email/<int:id>/delete', email.deleta_email, name='deleta-email'),
    path('email/<int:cliente_id>/create', email.novo_email, name='novo_email'),

    path('telefone/<int:id>/delete', telefone.deleta_telefone, name='deleta-telefone'),
    path('telefone/<int:cliente_id>/create', telefone.novo_telefone, name='novo_telefone'),

    path('endereco/<int:id>/delete', endereco.delete_endereco, name='delete-endereco'),
    path('endereco/<int:cliente_id>/create', endereco.novo_endereco, name='novo-endereco'),

    path('referencias/', referencias.referencias, name='referencias'),
    path('banco/', referencias.banco_detail, name='banco_novo'),
    path('banco/<int:banco_id>/', referencias.banco_detail, name='banco_detail'),

    # ── Novas rotas: Importação CSV ──
    path('importar/', importar.importar_clientes_view, name='importar_clientes'),
    path('importar_csv/', importar.importar_csv, name='importar_csv'),

    # ── Importação CSV: Endereços ──
    path('importar_enderecos_csv/', importar.importar_enderecos_csv, name='importar_enderecos_csv'),

    # ── Importação CSV: Financeiro ──
    path('importar_vinculo_csv/',   importar.importar_vinculo_csv,   name='importar_vinculo_csv'),
    path('importar_financeiro_csv/', importar.importar_financeiro_csv, name='importar_financeiro_csv'),
    path('importar_dividas_csv/',   importar.importar_dividas_csv,   name='importar_dividas_csv'),

    # ── Importação CSV: Veiculos ──
    path('importar_veiculos_csv/', importar.importar_veiculos_csv, name='importar_veiculos_csv')
]