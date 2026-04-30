from django.contrib.auth.models import User
from django.http import Http404
from .models import Empresa, ViewPermission
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.urls import resolve

from config import settings


class EmpresaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            return self.get_response(request)

        host = request.get_host().split(":")[0]
        partes = host.split(".")

        # Precisa ter pelo menos 3 partes: subdominio.dominio.tld
        if len(partes) < 2:
            raise Http404("Subdomínio obrigatório")

        subdominio = partes[0]

        try:
            empresa = Empresa.objects.get(
                subdominio=subdominio,
                ativa=True
            )
            request.empresa = empresa
        except Empresa.DoesNotExist:
            raise Http404("Empresa não encontrada")

        if request.user.is_authenticated:
            request.user = (
                User.objects
                .select_related('agente__carteira__empresa', 'agente__equipe', 'agente__perfil')
                .get(pk=request.user.pk)
            )

        return self.get_response(request)


PUBLIC_VIEWS = [
    'login_template',
    'login',
    'logout',
]

def get_permissions():
    perms = cache.get('view_permissions')

    if not perms:
        perms = {
            p.url_name: p.roles
            for p in ViewPermission.objects.all()
        }
        cache.set('view_permissions', perms, 60)

    return perms


class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # 🔥 ignora static e media
        if request.path.startswith(settings.STATIC_URL):
            return self.get_response(request)

        if request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            resolver = resolve(request.path_info)
            view_name = resolver.view_name
        except:
            return self.get_response(request)



        # 🔥 1. libera views públicas
        if view_name in PUBLIC_VIEWS:
            return self.get_response(request)

        # 🔥 2. usuário não logado → deixa seguir (login_required cuida)
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 🔥 3. sem agente → ignora
        agente = getattr(request.user.agente, 'agente', None)
        if not agente:
            return self.get_response(request)

        perfil = getattr(agente, 'perfil', None)
        role = getattr(perfil, 'codigo', None)

        # 🔥 4. ADM bypass global
        if role == 'ADM':
            return self.get_response(request)

        # 🔥 5. valida permissões
        perms = get_permissions()
        roles = perms.get(view_name)

        if roles is None:
            raise PermissionDenied

        if role not in roles:
            raise PermissionDenied

        return self.get_response(request)