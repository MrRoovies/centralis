from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Campanha, CampanhaAgente, CampanhaCliente


# ========================
# Inline CampanhaAgente
# ========================
class CampanhaAgenteInline(admin.TabularInline):
    model = CampanhaAgente
    extra = 0
    fields = ('agente', 'ativo')


# ========================
# Inline CampanhaCliente
# ========================
class CampanhaClienteInline(admin.TabularInline):
    model = CampanhaCliente
    extra = 0
    fields = ('cliente', 'agente_responsavel', 'situacao', 'prioridade', 'tentativas', 'ultima_tentativa')
    readonly_fields = ('tentativas', 'ultima_tentativa')
    show_change_link = True


# ========================
# Admin Campanha
# ========================
@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'carteira', 'modo_atendimento', 'metodo_distribuicao', 'distribuicao_ativa', 'created_at')
    list_filter = ('empresa', 'carteira', 'modo_atendimento', 'metodo_distribuicao', 'distribuicao_ativa')
    search_fields = ('nome', 'carteira__nome', 'empresa__nome')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    inlines = [CampanhaAgenteInline, CampanhaClienteInline]


# ========================
# Admin CampanhaAgente
# ========================
@admin.register(CampanhaAgente)
class CampanhaAgenteAdmin(admin.ModelAdmin):
    list_display = ('campanha', 'agente', 'ativo')
    list_filter = ('ativo', 'campanha__carteira', 'campanha')
    search_fields = ('campanha__nome', 'agente__usuario__username', 'agente__usuario__first_name')
    list_editable = ('ativo',)


# ========================
# Admin CampanhaCliente
# ========================
@admin.register(CampanhaCliente)
class CampanhaClienteAdmin(admin.ModelAdmin):
    list_display = ('campanha', 'cliente', 'agente_responsavel', 'situacao', 'prioridade', 'tentativas', 'ultima_tentativa')
    list_filter = ('campanha', 'situacao', 'campanha__carteira')
    search_fields = ('cliente__nome', 'cliente__documento', 'campanha__nome')
    readonly_fields = ('tentativas', 'ultima_tentativa')
    ordering = ('campanha', 'prioridade')