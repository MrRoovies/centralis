# core/context_menu.py
from django.urls import reverse

def get_menu(agente):
    perfil = getattr(agente, 'perfil', None)
    role = getattr(perfil, 'codigo', None)

    print(perfil, role)

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
            "roles": ["ADM", "DIRETOR", "GERENTE", "SUPERVISOR", "AGENTE"],
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
            "roles": ["ADM", "DIRETOR", "GERENTE"],
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
        if item.get("roles") and role not in item["roles"]:
            continue

        item_copy = item.copy()

        # 🔥 resolve url automaticamente
        if "url_name" in item:
            item_copy["url"] = reverse(item["url_name"])

        if "children" in item:
            filhos = []
            for child in item["children"]:
                child_copy = child.copy()

                if "url_name" in child:
                    child_copy["url"] = reverse(child["url_name"])

                filhos.append(child_copy)

            item_copy["children"] = filhos

        menu_final.append(item_copy)

    return menu_final