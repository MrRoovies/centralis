from django.db import models

# Create your models here.
class Empresa(models.Model):
    nome = models.CharField(max_length=150, blank=False, null=False)
    cnpj = models.SlugField(max_length=14, blank=True, null=True)
    subdominio = models.SlugField(unique=True, blank=False, null=False)
    ativa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome}"