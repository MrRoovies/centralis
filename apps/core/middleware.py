from django.contrib.auth.models import User
from django.http import Http404
from .models import Empresa

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