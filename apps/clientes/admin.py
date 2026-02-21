from django.contrib import admin

# Register your models here.
from .models import Cliente
# Register your models here.
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa',
        'documento', 'nome', 'tipo_pessoa', 'rg',
        'data_nascimento', 'nome_mae', 'nome_pai',
        'estado_civil', 'criado_em', 'atualizado_em']
    list_filter = ['empresa', 'documento']
admin.site.register(Cliente, ClienteAdmin)