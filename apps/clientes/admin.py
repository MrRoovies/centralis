from django.contrib import admin

# Register your models here.
from .models import Cliente, Email, Telefone, Endereco

class ClienteAdmin(admin.ModelAdmin):
    list_display = ['id', 'empresa',
        'documento', 'nome', 'tipo_pessoa', 'rg',
        'data_nascimento', 'nome_mae', 'nome_pai',
        'estado_civil', 'criado_em', 'atualizado_em']
    list_filter = ['empresa', 'documento']
admin.site.register(Cliente, ClienteAdmin)

class EmailAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente',
        'email', 'tipo', 'created_at', 'ativo']
    list_editable = ['ativo']
admin.site.register(Email, EmailAdmin)

class TelefoneAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente',
        'telefone', 'tipo', 'whats_app']
admin.site.register(Telefone, TelefoneAdmin)

class EnderecoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente',
        'logradouro', 'numero', 'bairro', 'cidade',
        'uf', 'cep', 'tipo']
admin.site.register(Endereco, EnderecoAdmin)