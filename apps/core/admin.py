from django.contrib import admin
from .models import Empresa, ViewPermission
# Register your models here.
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'cnpj', 'subdominio', 'ativa', 'created_at']
admin.site.register(Empresa, EmpresaAdmin)


@admin.register(ViewPermission)
class ViewPermissionAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'url_name', 'roles')