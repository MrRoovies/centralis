from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Lower

# Create your models here.
class Empresa(models.Model):
    nome = models.CharField(max_length=150, blank=False, null=False)
    cnpj = models.CharField(max_length=14, blank=True, null=True)
    subdominio = models.SlugField(unique=True, blank=False, null=False)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("nome"),
                name="unique_nome_case_insensitive"
            ),
            UniqueConstraint(
                fields=["cnpj"],
                condition=Q(cnpj__isnull=False),
                name="unique_cnpj_not_null"
            )
        ]

    def __str__(self):
        return f"{self.nome}"


class ViewPermission(models.Model):
    url_name = models.CharField(max_length=100)  # ex: 'relatorios'
    roles = models.JSONField(default=list)       # ['ADM', 'SUPERVISOR']
    app_name = models.CharField(max_length=100, null=True) # ex: clientes, agendas

    def __str__(self):
        return f"{self.url_name} -> {self.roles}"