from apps.core.responses.pattern import ResponsePattern
from apps.usuarios.models import Perfil
from django.contrib.auth.models import User, Group
from django.db import transaction


class PerfilService:

    @staticmethod
    def detalhes(perfil_id, empresa):
        if perfil_id:
            perfil = Perfil.objects.get(pk=perfil_id, empresa=empresa)
            data = {
                'id': perfil.id,
                'codigo': perfil.codigo,
                'escopo': perfil.escopo,
                'grupo_id': perfil.grupo_id,
                'ativo': perfil.ativo,
            }
        else:
            data = {}
        return data

    @staticmethod
    def campos_obrigatorios(data):
        for k, v in data.items():
            if k == 'criar_grupo_nome':
                continue
            if not v:
                return ResponsePattern.error('perfil', [f"{k.title()} não pode ser vazio."])

        return ResponsePattern.success('perfil', ['Ok'])


    @staticmethod
    def cria_ou_edita(data, perfil_id, empresa):
        codigo = data.get('codigo').strip()
        escopo = data.get('escopo').strip()
        grupo_id = data.get('grupo_id')
        ativo = data.get('ativo', True)
        criar_grupo_nome = data.get('criar_grupo_nome').strip()
        grupo = Group.objects.get(pk=grupo_id)

        # Resolve o grupo: cria novo ou usa existente
        if criar_grupo_nome:
            return ResponsePattern.error('group', ['Não é possível criar novo Grupo no momento'])
        #    grupo, _ = Group.objects.get_or_create(name=criar_grupo_nome)
        #elif grupo_id:
        #    grupo = get_object_or_404(Group, pk=grupo_id)

        try:
            with transaction.atomic():
                if perfil_id:
                    perfil = Perfil.objects.get(pk=perfil_id, empresa=empresa)
                    perfil.codigo = codigo
                    perfil.escopo = escopo
                    perfil.grupo = grupo
                    perfil.ativo = ativo
                    perfil.save()
                    msg = ['Perfil atualizado com sucesso!']

                else:
                    Perfil.objects.create(
                        empresa=empresa,
                        codigo=codigo,
                        escopo=escopo,
                        grupo=grupo,
                        ativo=ativo,
                    )
                    msg = ['Perfil criado com sucesso!']

                return ResponsePattern.success('perfil', msg)

        except Exception as e:
            return ResponsePattern.error('perfil', [str(e)])


    @staticmethod
    def criar_grupo_nome(criar_grupo_nome):
        pass
