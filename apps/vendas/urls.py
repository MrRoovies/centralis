from django.urls import path
from .views import contratos, contratos_edicao

app_name = 'vendas'

urlpatterns = [
    path('novo_contrato', contratos.registrar_venda, name='novo_contrato'),
    path('parceiros/', contratos.get_parceiros, name='get_parceiros'),
    path('produtos/', contratos.get_produtos, name='get_produtos'),
    path('ofertas/', contratos.get_ofertas, name='get_ofertas'),

    # ── Edicao ──
    path('<int:venda_id>/valores/', contratos_edicao.editar_valores, name='editar_valores'),
    path('<int:venda_id>/oferta/', contratos_edicao.editar_oferta, name='editar_oferta'),
    path('<int:venda_id>/responsavel/', contratos_edicao.responsavel, name='responsavel'),
    path('<int:venda_id>/comentario_e_esteira/', contratos_edicao.comentario_e_esteira, name='comentario_e_esteira'),

]