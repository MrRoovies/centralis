from django.contrib import admin

# Register your models here.
from .models import Cliente, Email, Telefone, Endereco, Bancos, Vinculo, Financeiro, Divida

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

class BancosAdmin(admin.ModelAdmin):
    list_display = ['id', 'cod_banco', 'nome_banco']
admin.site.register(Bancos, BancosAdmin)

class FinanceiroInline(admin.TabularInline):
    model = Financeiro
    extra = 0

    fields = (
        'referencia',
        'salario',
        'margem_consig',
        'margem_ct',
        'margem_ct_bn',
        'created_at',
    )

    readonly_fields = ('created_at',)

    ordering = ('-referencia',)

    show_change_link = True


class DividaInline(admin.TabularInline):
    model = Divida
    extra = 0

    fields = (
        'referencia',
        'banco',
        'rubrica',
        'Tipo',
        'saldo_devedor',
        'prazo_faltante',
        'contrato',
        'taxa',
        'created_at',
    )

    readonly_fields = ('created_at',)

    ordering = ('-referencia',)

    show_change_link = True


# =========================
# VINCULO
# =========================

@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'empresa',
        'cliente',
        'matricula',
        'convenio',
        'orgao',
        'sit_func',
        'created_at',
    )

    search_fields = (
        'cliente__nome',
        'cliente__cpf',
        'matricula',
        'instituidor',
        'convenio',
        'orgao',
    )

    list_filter = (
        'empresa',
        'convenio',
        'orgao',
        'sit_func',
        'created_at',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    list_select_related = (
        'empresa',
        'cliente',
    )

    inlines = [
        FinanceiroInline,
        DividaInline,
    ]


# =========================
# FINANCEIRO
# =========================

@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'empresa',
        'vinculo',
        'referencia',
        'salario',
        'margem_consig',
        'margem_ct',
        'margem_ct_bn',
    )

    search_fields = (
        'vinculo__cliente__nome',
        'vinculo__cliente__cpf',
        'vinculo__matricula',
    )

    list_filter = (
        'empresa',
        'referencia',
        'created_at',
    )

    autocomplete_fields = (
        'vinculo',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = (
        '-referencia',
    )

    list_select_related = (
        'empresa',
        'vinculo',
        'vinculo__cliente',
    )


# =========================
# DIVIDA
# =========================

@admin.register(Divida)
class DividaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'empresa',
        'vinculo',
        'banco',
        'rubrica',
        'Tipo',
        'saldo_devedor',
        'prazo_faltante',
        'contrato',
        'referencia',
    )

    search_fields = (
        'vinculo__cliente__nome',
        'vinculo__cliente__cpf',
        'vinculo__matricula',
        'contrato',
        'banco',
    )

    list_filter = (
        'empresa',
        'banco',
        'rubrica',
        'referencia',
        'created_at',
    )

    autocomplete_fields = (
        'vinculo',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = (
        '-referencia',
    )

    list_select_related = (
        'empresa',
        'vinculo',
        'vinculo__cliente',
    )