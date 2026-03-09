from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json


# Create your views here.
def login_template(request):
    return render(request, "registration/login.html")

@require_http_methods(["POST"])
def login_view(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
            empresa=request.empresa
        )

        if user is None:
            return render(
                request,
                "registration/login.html",
                {"error": "Usuário ou senha incorretos"}
            )

        login(request, user)
        return redirect("/home")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Método inválido"}, status=400)


@login_required
def home(request):
    return render(request, 'home.html')