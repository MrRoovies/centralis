# apps/core/utils.py

from django.urls import get_resolver, URLPattern, URLResolver


def listar_urls():
    resolver = get_resolver()
    urls = []

    def extrair(patterns, prefix=''):
        for p in patterns:
            # 🔥 ignora admin
            if isinstance(p, URLResolver) and p.namespace == 'admin':
                continue

            # 👉 URL normal (path)
            if isinstance(p, URLPattern):
                if p.name:
                    full_name = f"{prefix}:{p.name}" if prefix else p.name
                    urls.append(full_name)

            # 👉 include()
            elif isinstance(p, URLResolver):
                ns = p.namespace or ''
                novo_prefixo = f"{prefix}:{ns}" if prefix and ns else ns or prefix
                extrair(p.url_patterns, novo_prefixo)

    extrair(resolver.url_patterns)
    return urls