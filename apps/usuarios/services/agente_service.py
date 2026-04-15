from apps.usuarios.models import Agente
from apps.core.regras_acesso import RegrasAcesso
from apps.core.responses.pattern import ResponsePattern
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.usuarios.models import Carteira, Equipe, Perfil


class AgenteService:
    @staticmethod
    def get_agentes(empresa):
        qs = (
            Agente.objects.filter(carteira__empresa=empresa)
            .select_related('usuario', 'perfil', 'carteira', 'equipe')
            .order_by('carteira__nome', 'usuario__first_name'))

        return qs

    @staticmethod
    def filtrar(qs, filtro, usuario):
        qs = RegrasAcesso(usuario).model_filter(qs)
        return qs.filter(**filtro)

    @staticmethod
    def campos_obrigatorios(data, empresa):
        for k, v in data.items():
            if k == 'email':
                continue
            if not data.get(k):
                return ResponsePattern.error(k, [f"{k} não pode ser vazio"])

        return AgenteService.registra_usuario(data, empresa)

    @staticmethod
    def registra_usuario(data, empresa):
        if User.objects.filter(username=data['username']).exists():
            return ResponsePattern.error('usuario', ['Usuário já existe.'])

        carteira = get_object_or_404(Carteira, pk=data['carteira_id'], empresa=empresa, ativo=True)
        equipe = get_object_or_404(Equipe, pk=data['equipe_id'], ativo=True)
        perfil = get_object_or_404(Perfil, pk=data['perfil_id'], ativo=True)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    email=data['email'],
                )
                if perfil.grupo:
                    user.groups.add(perfil.grupo)
                    user.save()

                Agente.objects.create(
                    usuario=user,
                    carteira=carteira,
                    equipe=equipe,
                    perfil=perfil,
                    cpf=data['cpf'],
                    nascimento=data['nascimento'],
                    email=data['email'],
                )
            return ResponsePattern.success('agente', ['Agente criado com sucesso!'])

        except Exception as e:
            return ResponsePattern.error('agente', [str(e)])

