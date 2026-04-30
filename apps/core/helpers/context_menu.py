# core/context_menu.py
from django.urls import reverse
from apps.core.middleware import get_permissions

def has_permission(agente, view_name):
    if not agente:
        return False

    perfil = getattr(agente, 'perfil', None)
    role = getattr(perfil, 'codigo', None)

    # 🔥 ADM bypass (mesma regra do middleware)
    if role == 'ADM':
        return True

    perms = get_permissions()
    roles = perms.get(view_name)

    if roles is None:
        return False

    return role in roles



def get_menu(agente):
    perfil = getattr(agente, 'perfil', None)
    role = getattr(perfil, 'codigo', None)

    MENU_CONFIG = [
        {
            "label": "Home",
            "url_name": "home",
            "icon": "🏠"
        },
        {
            "label": "Cadastrar Cliente",
            "url_name": "clientes:cliente_novo",
            "icon": "👤"
        },
        {
            "label": "Atender Campanhas",
            "url_name": "campanhas:painel_campanhas",
            "icon": "📋"
        },
        {
            "label": "Relatórios",
            "subgroup": "relatorios",
            "icon": "📊",
            "children":
                [
                    {"label": "Vendas", "url_name": "relatorios:relatorio_vendas"},
                    {"label": "Agendas", "url_name": "relatorios:lista_agendas"},
                ],
        },
        {
            "label": "Administração",
            "subgroup": "admin",
            "icon": "⚙️",
            "children": [
                {"label": "Agentes", "url_name": "usuarios:lista_agentes"},
                {"label": "Perfis e Equipes", "url_name": "usuarios:lista_configuracoes"},
                {"label": "Campanhas Admin", "url_name": "campanhas:admin_campanhas"},
                {"label": "Importar Clientes", "url_name": "clientes:importar_clientes"},
                {"label": "Vendas Admin", "url_name": "vendas:lista_vendas_admin"},
                {"label": "Permissioes Admin", "url_name": "usuarios:view_permissions_list"}
            ],
        },
    ]

    menu_final = []

    for item in MENU_CONFIG:
        item_copy = item.copy()

        # 🔥 ITEM SIMPLES (sem filhos)
        if "url_name" in item and "children" not in item:
            if not has_permission(agente, item["url_name"]):
                continue

            item_copy["url"] = reverse(item["url_name"])

        # 🔥 ITEM COM FILHOS (submenu)
        if "children" in item:
            filhos = []

            for child in item["children"]:
                if not has_permission(agente, child["url_name"]):
                    continue

                child_copy = child.copy()
                child_copy["url"] = reverse(child["url_name"])
                filhos.append(child_copy)

            # 🔥 só adiciona o grupo se tiver pelo menos 1 filho visível
            if not filhos:
                continue

            item_copy["children"] = filhos

        menu_final.append(item_copy)