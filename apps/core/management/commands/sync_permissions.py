
from django.core.management.base import BaseCommand
from apps.core.models import ViewPermission
from apps.core.utils import listar_urls


class Command(BaseCommand):
    help = 'Sincroniza URLs com ViewPermission'

    def handle(self, *args, **kwargs):
        urls = listar_urls()
        urls_set = set(urls)

        criados = 0

        # 🔥 cria os que não existem
        for url in urls:
            obj, created = ViewPermission.objects.get_or_create(
                url_name=url,
                defaults={"roles": ["ADM"]}
            )
            if created:
                criados += 1

        # 🔥 remove os que não existem mais no projeto
        deletados, _ = ViewPermission.objects.exclude(
            url_name__in=urls_set
        ).delete()

        self.stdout.write(self.style.SUCCESS(
            f'{criados} criados | {deletados} removidos'
        ))