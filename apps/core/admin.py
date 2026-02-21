from django.contrib import admin
from .models import Empresa
# Register your models here.
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'cnpj', 'subdominio', 'ativa', 'created_at']
admin.site.register(Empresa, EmpresaAdmin)