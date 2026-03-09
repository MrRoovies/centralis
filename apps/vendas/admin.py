from django.contrib import admin
from .models import Parceiro, Produto, Oferta, Esteira, Venda, HistVenda


@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "ativo")
    list_filter = ("empresa", "ativo")
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "ativo")
    list_filter = ("empresa", "ativo")
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = (
        "produto",
        "parceiro",
        "empresa",
        "prazo_min",
        "prazo_max",
        "comissao",
        "ativo"
    )

    list_filter = (
        "empresa",
        "produto",
        "parceiro",
        "ativo"
    )

    search_fields = (
        "produto__nome",
        "parceiro__nome"
    )

    ordering = ("produto", "parceiro")


@admin.register(Esteira)
class EsteiraAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "tipo",
        "empresa",
        "carteira",
        "ordem",
        "ativo"
    )

    list_filter = (
        "empresa",
        "carteira",
        "tipo",
        "ativo"
    )

    search_fields = ("nome",)

    ordering = ("empresa", "carteira", "ordem")


class HistVendaInline(admin.TabularInline):
    model = HistVenda
    extra = 0
    readonly_fields = (
        "esteira",
        "usuario",
        "comentario",
        "data"
    )
    can_delete = False


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        'contrato',
        "cliente",
        "oferta",
        "usuario",
        "esteira",
        "valor",
        "prazo",
        "data_venda"
    )

    list_filter = (
        "empresa",
        "esteira",
        "oferta__produto",
        "oferta__parceiro",
        "usuario",
        "data_venda"
    )

    search_fields = (
        'contrato',
        "cliente__nome",
        "cliente__documento"
    )

    ordering = ("-data_venda",)

    inlines = [HistVendaInline]


@admin.register(HistVenda)
class HistVendaAdmin(admin.ModelAdmin):
    list_display = (
        "venda",
        "esteira",
        "usuario",
        "data"
    )

    list_filter = (
        "esteira",
        "usuario",
        "data"
    )

    search_fields = (
        "venda__cliente__nome",
    )

    ordering = ("-data",)