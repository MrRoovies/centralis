from django.urls import path
from .views import relatorios

app_name = 'relatorios'

urlpatterns = [
    path('relatorio_vendas/', relatorios.relatorio_vendas, name='relatorio_vendas'),
]