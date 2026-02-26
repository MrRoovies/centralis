from django.urls import path
from .views import cliente, email, telefone

app_name = 'clientes'

urlpatterns = [
    path(r'search_cliente', cliente.search_cliente, name='search_cliente'),
    path('cliente_novo', cliente.cliente_novo, name='cliente_novo'),
    path('cliente/<int:id>', cliente.cliente, name='cliente'),
    path('cliente/<int:cliente_id>/edit', cliente.edita_cliente, name='edita_cliente'),

    path('email/<int:id>/delete', email.deleta_email, name='deleta-email'),
    path('email/<int:cliente_id>/create', email.novo_email, name='novo_email'),

    path('telefone/<int:id>/delete', telefone.deleta_telefone, name='deleta-telefone')
]