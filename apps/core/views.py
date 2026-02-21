from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import json

# Create your views here.
def login_template(request):
    return render(request, "registration/login.html")

@require_POST
def login_view(request):
    if request.body:
        data = json.loads(request.body)
        username = data.get('text_user')
        password = data.get('text_pass')

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({'status': 'error', 'message': 'Usuário ou senha incorretos'}, status=403)

        login(request, user)
        return JsonResponse({'status': 'success', 'message': 'Bem vindo!'}, status=200)

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Método inválido"}, status=400)


@login_required
def home(request):
    return render(request, 'home.html')