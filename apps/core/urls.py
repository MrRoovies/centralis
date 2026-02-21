
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_template, name="login_template"),
    path('login', views.login_view, name="login"),
    path('logout', views.logout_view, name="logout"),
    path('home', views.home, name="home"),
]