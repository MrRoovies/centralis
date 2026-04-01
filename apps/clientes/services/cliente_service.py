from apps.clientes.models import Cliente
from django.db.models import Q
import json
class ClienteService:
    @staticmethod
    def buscar_cliente(dado_pesquisa, empresa):
        qs = Cliente.objects.for_empresa(empresa)
        chave, valor = next(iter(dado_pesquisa.items()))
        modo_pesquisa = {
            'nome': lambda: ClienteService.buscar_por_nome(qs, valor),
            'telefone': lambda: ClienteService.buscar_por_telefone(qs, valor),
            'email': lambda: ClienteService.buscar_por_email(qs, valor),
        }

        func = modo_pesquisa.get(chave)

        if func:
            qs = func()
        else:
            qs = qs.filter(**{chave: valor})

        return list(qs.values('id', 'nome', 'documento'))

    @staticmethod
    def buscar_por_nome(queryset, nome):
        partes = nome.split()
        filtro = Q()
        for parte in partes:
            filtro &= Q(nome__icontains=parte)

        return queryset.filter(filtro)

    @staticmethod
    def buscar_por_telefone(queryset, telefone):
        filtro = Q(telefones__telefone__icontains=telefone)
        return queryset.filter(filtro)


    @staticmethod
    def buscar_por_email(queryset, email):
        filtro = Q(emails__email__icontains=email)
        return queryset.filter(filtro)

    @staticmethod
    def buscar_por_documento(empresa, documento):
        return Cliente.objects.for_empresa(empresa) \
            .filter(documento=documento) \
            .values('id') \
            .first()