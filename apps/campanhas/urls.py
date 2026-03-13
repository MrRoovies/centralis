from .views import campanhas
from django.urls import path, include

urlpatterns = [
    path('', campanhas.painel_campanhas, name="painel_campanhas"),
]
