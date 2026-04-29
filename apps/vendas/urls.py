from django.urls import path
from .views import contratos, contratos_edicao, vendas_admin

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

    # ── Criação de Recursos ──
    path('admin/vendas', vendas_admin.lista_vendas_admin, name='lista_vendas_admin'),
    path('admin/parceiro/<int:parceiro_id>/', vendas_admin.parceiro_detail, name='parceiro_detail'),
    path('admin/produto/<int:produto_id>/', vendas_admin.produto_detail, name='produto_detail'),
    path('admin/oferta/<int:oferta_id>/', vendas_admin.oferta_detail, name='oferta_detail'),
    path('admin/esteira/<int:esteira_id>/', vendas_admin.esteira_detail, name='esteira_detail'),

    # ── Toogle ──
    path('admin/parceiro/<int:parceiro_id>/toggle/', vendas_admin.parceiro_toggle, name='parceiro_toggle'),
    path('admin/produto/<int:produto_id>/toggle/', vendas_admin.produto_toggle, name='produto_toggle'),
    path('admin/oferta/<int:oferta_id>/toggle/', vendas_admin.oferta_toggle, name='oferta_toggle'),
    path('admin/esteira/<int:esteira_id>/toggle/', vendas_admin.esteira_toggle, name='esteira_toggle'),

    # ── Novo ──
    path('admin/parceiro/', vendas_admin.parceiro_detail, name='parceiro'),
    path('admin/produto/', vendas_admin.produto_detail, name='produto'),
    path('admin/oferta/', vendas_admin.oferta_detail, name='oferta'),
    path('admin/esteira/', vendas_admin.esteira_detail, name='esteira'),

]
