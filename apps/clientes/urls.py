from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('search_cliente', views.search_cliente, name='search_cliente'),
    path('cliente_novo', views.cliente_novo, name='cliente_novo'),
    path('cliente/<int:id>', views.cliente, name='cliente'),
]