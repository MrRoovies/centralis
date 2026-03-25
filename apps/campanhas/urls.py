from .views import campanhas
from django.urls import path

app_name = 'campanhas'

urlpatterns = [
    path('', campanhas.painel_campanhas, name="painel_campanhas"),
    path('atender/<int:id_campanha>', campanhas.atender, name="atender"),
    path('proximo_cliente/<int:id_campanha>/', campanhas.proximo_cliente, name="proximo_cliente"),
    path('adiantar_agenda/<int:id_campanha>/', campanhas.adiantar_agenda, name="adiantar_agenda"),
]
