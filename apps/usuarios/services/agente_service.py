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
            Agente.objects.filter(perfil__empresa=empresa)
            .select_related('usuario', 'perfil', 'carteira', 'equipe')
            .order_by('carteira__nome', 'usuario__first_name'))
        return qs

    @staticmethod
    def filtrar(qs, filtro, usuario):
        qs = RegrasAcesso(usuario).model_filter(qs)
        return qs.filter(**filtro)

    @staticmethod
    def campos_obrigatorios(data):
        for k, v in data.items():
            if k in ['email', 'senha']:
                continue
            if not data.get(k):
                return ResponsePattern.error(k, [f"{k} não pode ser vazio"])
        return ResponsePattern.success('filtro', ['Filtros pareados com sucesso'])

    @staticmethod
    def registra_usuario(data, empresa):

        if User.objects.filter(username=data['username']).exists():
            return ResponsePattern.error('usuario', ['Usuário já existe.'])

        try:
            perfil = Perfil.objects.get(
                pk=data['perfil_id'],
                empresa=empresa,
                ativo=True
            )
        except Perfil.DoesNotExist:
            return ResponsePattern.error('perfil', ['Perfil inválido'])

        equipe = None

        if perfil.codigo != 'ADM':

            campos = AgenteService.campos_obrigatorios(data)
            if not campos['success']:
                return campos

            carteira = Carteira.objects.filter(
                pk=data.get('carteira_id'),
                empresa=empresa,
                ativo=True
            ).first()

            if not carteira:
                return ResponsePattern.error('carteira', ['Carteira inválida'])

            equipe = Equipe.objects.filter(
                pk=data.get('equipe_id'),
                empresa=empresa,
                ativo=True
            ).first()

            if not equipe:
                return ResponsePattern.error('equipe', ['Equipe inválida'])

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

                Agente.objects.create(
                    usuario=user,
                    carteira=carteira,
                    equipe=equipe,
                    perfil=perfil,
                    cpf=data['cpf'],
                    nascimento=data['nascimento'],
                    email=data['email'],
                )

            return ResponsePattern.success('agente', ['✓ Agente cadastrado com sucesso!'])

        except Exception as e:
            # ideal: logar isso aqui
            return ResponsePattern.error('agente', ['Erro interno ao criar usuário'])

    @staticmethod
    def edita_usuario(dados, agente, empresa):

        try:
            perfil = Perfil.objects.get(
                pk=dados['perfil_id'],
                empresa=empresa,
                ativo=True
            )
        except Perfil.DoesNotExist:
            return ResponsePattern.error('perfil', ['Perfil inválido'])

        try:
            carteira = Carteira.objects.filter(
                pk=dados.get('carteira_id'),
                empresa=empresa,
                ativo=True
            ).first()
        except:
            carteira = None

        equipe = None        

        if perfil.codigo != 'ADM':

            campos = AgenteService.campos_obrigatorios(dados)
            if not campos['success']:
                return campos

            equipe = Equipe.objects.filter(
                pk=dados.get('equipe_id'),
                empresa=empresa,
                ativo=True
            ).first()

            if not equipe:
                return ResponsePattern.error('equipe', ['Equipe inválida'])

        try:
            with transaction.atomic():

                user = agente.usuario
                user.first_name = dados.get('first_name', user.first_name)
                user.last_name = dados.get('last_name', user.last_name)

                senha = dados.get('senha')
                if senha:
                    user.set_password(senha)

                user.save()

                agente.email = dados.get('email', agente.email)
                agente.cpf = dados.get('cpf', agente.cpf)
                agente.perfil = perfil
                agente.equipe = equipe
                agente.carteira = carteira
                agente.save()

            return ResponsePattern.success('agente', ['✓ Agente atualizado com sucesso!'])

        except Exception:
            # ideal logar aqui
            return ResponsePattern.error('agente', ['Erro interno ao atualizar agente'])