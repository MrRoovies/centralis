from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Agente, Carteira, Equipe, Perfil, AgentePerfil


# ========================
# Inline para AgentePerfil
# ========================
class AgentePerfilInline(admin.TabularInline):
    model = AgentePerfil
    extra = 0
    fields = ('perfil', 'ativo', 'data_inicio', 'data_fim')
    readonly_fields = ('data_inicio',)


# ========================
# Admin Agente
# ========================
@admin.register(Agente)
class AgenteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'perfil', 'carteira', 'equipe', 'idade', 'cpf', 'email')
    list_filter = ('perfil', 'equipe', 'carteira')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'cpf', 'email')
    inlines = [AgentePerfilInline]
    ordering = ('carteira',)

    def idade(self, obj):
        return obj.idade()
    idade.short_description = 'Idade'


# ========================
# Admin Carteira
# ========================
@admin.register(Carteira)
class CarteiraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'ativo')
    list_filter = ('empresa', 'ativo')
    search_fields = ('nome', 'empresa__nome')


# ========================
# Admin Equipe
# ========================
@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'responsavel', 'ativo', 'data_create')
    list_filter = ('ativo',)
    search_fields = ('nome', 'responsavel__username')


# ========================
# Admin Perfil
# ========================
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'grupo', 'ativo', 'data_create')
    list_filter = ('ativo', 'grupo')
    search_fields = ('codigo', 'grupo__name')


# ========================
# Admin AgentePerfil
# ========================
@admin.register(AgentePerfil)
class AgentePerfilAdmin(admin.ModelAdmin):
    list_display = ('agente', 'perfil', 'ativo', 'data_inicio', 'data_fim')
    list_filter = ('ativo', 'perfil')
    search_fields = ('agente__usuario__username', 'perfil__codigo')
    ordering = ('agente', 'perfil')