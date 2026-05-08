from apps.core.responses.pattern import ResponsePattern
from apps.usuarios.models import Perfil
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.db.models import Value, Q
from django.db.models.functions import Concat
from apps.usuarios.models import Equipe, Agente, Carteira
from apps.agenda.models import Situacao, CarteiraSituacao


def campos_obrigatorios(data, local, campos):
    for k, v in data.items():
        if not k in campos:
            continue
        if not v and k != 'ativo':
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


class CarteiraService:
    @staticmethod
    def detalhes(carteira_id, empresa):
        situacoes = (
            Situacao.objects
            .filter(empresa=empresa)
            .order_by('nome')
        )

        if carteira_id:
            carteira = Carteira.objects.get(empresa=empresa, pk=carteira_id)

            situacoes_ativas = set(
                CarteiraSituacao.objects
                .filter(carteira=carteira)
                .values_list('situacao_id', flat=True)
            )

            situacoes_list = [
                {
                    'id': sit.id,
                    'nome': sit.nome,
                    'ativo_carteira': 'checked' if sit.id in situacoes_ativas else ''
                }
                for sit in situacoes
            ]

            data = {
                'id': carteira.id,
                'nome': carteira.nome,
                'ativo': carteira.ativo,
                'situacoes': situacoes_list,
            }

            return ResponsePattern.success_data({'carteira': data})

        data = {
            'situacoes': list(situacoes.values('id', 'nome'))
        }

        return ResponsePattern.success_data({'carteira': data})


    @staticmethod
    def cria_ou_edita(data, carteira_id, empresa):
        try:
            with transaction.atomic():
                if carteira_id:
                    carteira = Carteira.objects.get(pk=carteira_id, empresa=empresa)
                    carteira.nome = data.get('nome').strip()
                    carteira.ativo = data.get('ativo')
                    carteira.save()
                    msg = ['Carteira atualizada com sucesso!']
                else:
                    carteira = Carteira.objects.create(
                        empresa=empresa,
                        nome=data.get('nome').strip(),
                        ativo=data.get('ativo'),
                    )
                    msg = ['Carteira criada com sucesso!']

                if 'situacoes' in data:
                    ids = set(map(int, data.get('situacoes', [])))

                    atuais = set(
                        CarteiraSituacao.objects
                        .filter(carteira=carteira)
                        .values_list('situacao_id', flat=True)
                    )

                    novos = ids - atuais

                    CarteiraSituacao.objects.bulk_create([
                        CarteiraSituacao(carteira=carteira, situacao_id=sid)
                        for sid in novos
                    ])

                    remover = atuais - ids

                    CarteiraSituacao.objects.filter(
                        carteira=carteira,
                        situacao_id__in=remover
                    ).delete()


            return ResponsePattern.success('carteira', msg)

        except Exception as e:
            return ResponsePattern.error('carteira', [str(e)])