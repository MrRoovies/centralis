
from functools import wraps
from django.core.exceptions import PermissionDenied

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            agente = getattr(request.user, 'agente', None)
            perfil = getattr(agente, 'perfil', None)
            role = getattr(perfil, 'codigo', None)

            if role not in roles:
                raise PermissionDenied  # 🔥 melhor que redirect

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator