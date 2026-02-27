from django.contrib import admin
from .models import Agenda, Acionamento, Situacao

# ===============================
# Inline do Acionamento para Agenda
# ===============================
class AcionamentoInline(admin.TabularInline):
    model = Acionamento
    extra = 0
    readonly_fields = ('data_acionamento',)
    fields = ('data_acionamento', 'data_finalizado', 'situacao', 'comentario')
    show_change_link = True

# ===============================
# Admin Agenda
# ===============================
@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'usuario', 'equipe', 'perfil', 'carteira',
        'telefone', 'situacao', 'agenda_ativa', 'data_entrada', 'data_hora_retorno', 'data_finalizado'
    )
    list_filter = ('usuario', 'equipe', 'perfil', 'carteira', 'agenda_ativa', 'situacao')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'telefone')
    readonly_fields = ('data_entrada',)
    inlines = [AcionamentoInline]
    ordering = ('-data_entrada',)

# ===============================
# Admin Acionamento
# ===============================
@admin.register(Acionamento)
class AcionamentoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'agenda', 'data_acionamento', 'data_finalizado', 'situacao', 'comentario'
    )
    list_filter = ('situacao', 'agenda__carteira')
    search_fields = ('agenda__usuario__username', 'agenda__telefone', 'comentario')
    readonly_fields = ('data_acionamento',)
    ordering = ('-data_acionamento',)

# ===============================
# Admin Situacao
# ===============================
@admin.register(Situacao)
class SituacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'carteira', 'ativo')
    list_filter = ('tipo', 'carteira', 'ativo')
    search_fields = ('nome',)
    ordering = ('tipo', 'nome')