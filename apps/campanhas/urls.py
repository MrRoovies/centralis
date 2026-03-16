from .views import campanhas
from django.urls import path

app_name = 'campanhas'

urlpatterns = [
    path('', campanhas.painel_campanhas, name="painel_campanhas"),
    path('atender<int:id_campanha>', campanhas.atender, name="atender"),
]
