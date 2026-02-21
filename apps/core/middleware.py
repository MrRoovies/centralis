from django.http import Http404
from .models import Empresa

class EmpresaMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        host = request.get_host().split(":")[0]
        partes = host.split(".")

        if len(partes) > 1:
            subdominio = partes[0]
        else:
            subdominio = None

        if subdominio and subdominio != "localhost":
            try:
                empresa = Empresa.objects.get(subdominio=subdominio)
                request.empresa = empresa
            except Empresa.DoesNotExist:
                raise Http404("Empresa não encontrada")
        else:
            request.empresa = None

        response = self.get_response(request)
        return response
