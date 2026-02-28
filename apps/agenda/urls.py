from django.urls import path
from .views import agenda_cliente

app_name = 'agenda'

urlpatterns = [
    path("historico/<int:cliente_id>/", agenda_cliente.hist_agenda_cliente, name="hist_agenda")
]