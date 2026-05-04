
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.core.models import Empresa
from apps.usuarios.models import Carteira

class Command(BaseCommand):
    help = 'Cria Empresa'

    def add_arguments(self, parser):
        parser.add_argument("--nome", required=True)
        parser.add_argument("--cnpj", required=False)
        parser.add_argument("--subdominio", required=True)


    def handle(self, *args, **options):
        nome = options["nome"]
        cnpj = options.get("cnpj")
        subdominio = options["subdominio"]

        # primeiro de tudo cria empresa
        empresa, create = Empresa.objects.get_or_create(
            subdominio=subdominio,
            defaults={
                "nome": nome,
                "cnpj": cnpj,
            }
        )
        if create:
            self.stdout.write(self.style.SUCCESS("Empresa criada!"))
        else:
            self.stdout.write(self.style.ERROR("Já existe uma empresa com esse subdomínio"))


    def create_carteira(self, empresa):
        carteira, create = Carteira.objects.get_or_create(
            nome="Admin",
        )


    def create_user(self):
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                "email": "admin@email.com",
                "is_staff": True,
                "is_superuser": True
            })

        if created:
            user.first_name = "Administrador"
            user.last_name = ""
            user.set_password = "admin123"
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{user.first_name} criado com sucesso!"))
        else:
            self.stdout.write(self.style.ERROR(f"{user.username} já existe!"))


    def create_equipe(self, user):
        # Cria equipe pq precisa da empresa
        pass

