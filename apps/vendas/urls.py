from django.contrib import admin
from django.urls import path, include
from .views import contratos

urlpatterns = [
    path('novo_contrato', contratos.registrar_venda, name='novo_contrato')
]