# apps/core/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmpresaBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, empresa=None, **kwargs):
        if not empresa:
            return None
        try:
            # Garante que o usuário pertence à empresa via agente
            user = User.objects.get(
                username=username,
                agente__carteira__empresa=empresa
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None