
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.core.models import Empresa
from apps.usuarios.models import Perfil, Agente

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
        empresa, created = Empresa.objects.get_or_create(
            subdominio=subdominio,
            defaults={
                "nome": nome,
                "cnpj": cnpj,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Empresa criada!"))
        else:
            self.stdout.write(self.style.WARNING("Já existe uma empresa com esse subdomínio"))

        perfil = self.create_perfil(empresa)
        user = self.create_user(empresa)
        self.create_agente(user, perfil)

        self.stdout.write(
            self.style.SUCCESS(
                f"Bootstrap concluído 🚀 | Empresa: {empresa.nome} | User: {user.username}"
            )
        )


    def create_perfil(self, empresa):
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        perfil, created = Perfil.objects.get_or_create(
            codigo="ADM",
            empresa=empresa,
            defaults={
                "escopo": "GLOBAL",
                "grupo": admin_group
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Perfil criada!"))
        else:
            self.stdout.write(self.style.WARNING("Já existe um perfil com esse nome"))
        return perfil

    def create_user(self, empresa):
        user, created = User.objects.get_or_create(
            username=f'admin_{empresa.subdominio}',
            defaults={
                "email": "admin@email.com",
                "is_staff": True,
                "is_superuser": True
            })

        if created:
            user.first_name = "Administrador"
            user.last_name = ""
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.SUCCESS(f"{user.first_name} criado com sucesso!"))
        else:
            self.stdout.write(self.style.WARNING(f"{user.username} já existe!"))
        return user

    def create_agente(self, user, perfil):
        agente, created = Agente.objects.get_or_create(
            usuario=user,
            defaults={
                "perfil":perfil,
                "email":user.email,
                "nascimento": '1987-03-15',
            }
        )

        if not created:
            agente.perfil = perfil
            agente.email = user.email
            agente.save()

        self.stdout.write(self.style.SUCCESS("Agente pronto!"))