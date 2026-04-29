from apps.core.helpers.context_menu import get_menu

def menu_context(request):
    if request.user.is_authenticated:
        return {
            "MENU_ITEMS": get_menu(request.user.agente)
        }
    return {}