from django.http import Http404
from .models import Empresa

class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

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

        return self.get_response(request)