from apps.core.responses.pattern import ResponsePattern
from apps.usuarios.models import Perfil
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Concat
from apps.usuarios.models import Equipe, Agente


def campos_obrigatorios(data, local, campos):
    for k, v in data.items():
        if not k in campos:
            continue
        if not v:
            return ResponsePattern.error(f'{local}', [f"{k.title()} não pode ser vazio."])
    return ResponsePattern.success(f'{local}', ['Ok'])


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
        """
           Por enquanto não vai funcionar
           Criação de gupos envolve permissões de acesso
           Preciso configurar as permissões antes.
        """
        pass

class EquipeService:
    @staticmethod
    def detalhes(equipe_id, empresa):
        try:
            supervisores = list(
                Agente.objects
                .filter(
                    carteira__empresa=empresa,
                    usuario__is_active=True,
                    perfil__codigo__in=['SUPERVISOR', 'DIRETOR', 'GERENTE']
                ).annotate(
                    nome=Concat(
                        'usuario__first_name',
                        Value(' '),
                        'usuario__last_name'
                    )
                )
                .values('usuario_id', 'nome', 'usuario__username')
                .order_by('nome')
            )

            if equipe_id:
                equipe = Equipe.objects.get(pk=equipe_id, empresa=empresa)
                data = {
                    'id': equipe.id,
                    'nome': equipe.nome,
                    'responsavel_id': equipe.responsavel_id,
                    'ativo': equipe.ativo,
                }
            else:
                data = {}
        except Exception as e:
            ResponsePattern.error('equipe', [str(e)])

        return ResponsePattern.success_data({'equipe': data, 'usuarios': supervisores})


    @staticmethod
    def cria_ou_edita(data, equipe_id, empresa):
        try:
            with transaction.atomic():
                usuario = User.objects.filter(
                    id=data.get('responsavel_id'),
                    agente__carteira__empresa=empresa
                ).first()

                if equipe_id:
                    equipe = Equipe.objects.get(pk=equipe_id, empresa=empresa)
                    equipe.nome = data.get('nome').strip()
                    equipe.responsavel = usuario
                    equipe.ativo = data.get('ativo')
                    equipe.save()
                    msg = ['Equipe atualizada com sucesso!']
                else:
                    Equipe.objects.create(
                        empresa=empresa,
                        nome=data.get('nome').strip(),
                        responsavel=usuario,
                        ativo=data.get('ativo'),
                    )
                    msg = ['Equipe criada com sucesso!']

            return ResponsePattern.success('equipe', msg)

        except Exception as e:
            return ResponsePattern.error('equipe', [str(e)])