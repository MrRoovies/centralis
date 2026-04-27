import re
from apps.clientes.models import Cliente, Telefone, Email

class Extrator:
    @staticmethod
    def _extrair_telefones(registro):
        """
        Lê telefone1/telefone1_tipo, telefone2/telefone2_tipo, telefone3/telefone3_tipo.
        Retorna lista de dicts válidos: [{'numero': '...', 'tipo': '...'}]
        """
        TIPOS_TELEFONE_VALIDOS = ['FIXO', 'CELULAR', 'CORPORATIVO']
        resultado = []
        for i in range(1, 4):
            numero = re.sub(r'\D', '', str(registro.get(f'telefone{i}', '')))
            tipo = str(registro.get(f'telefone{i}_tipo', '')).upper().strip()

            if not numero:
                continue
            if len(numero) not in (10, 11):
                continue  # Inválido — ignora silenciosamente (o front já avisou)

            # Tipo: se ausente ou inválido, infere pelo tamanho
            if tipo not in TIPOS_TELEFONE_VALIDOS:
                tipo = 'CELULAR' if len(numero) == 11 else 'FIXO'

            resultado.append({'numero': numero, 'tipo': tipo})

        return resultado

    @staticmethod
    def _extrair_emails(registro):
        """
        Lê email1/email1_tipo, email2/email2_tipo, email3/email3_tipo.
        Retorna lista de dicts válidos: [{'email': '...', 'tipo': '...'}]
        """
        TIPOS_EMAIL_VALIDOS = ['PESSOAL', 'CORPORATIVO']
        resultado = []
        for i in range(1, 4):
            mail = str(registro.get(f'email{i}', '')).strip()
            tipo = str(registro.get(f'email{i}_tipo', '')).upper().strip()

            if not mail:
                continue
            if '@' not in mail or '.' not in mail.split('@')[-1]:
                continue  # Inválido — ignora silenciosamente

            if tipo not in TIPOS_EMAIL_VALIDOS:
                tipo = 'PESSOAL'

            resultado.append({'email': mail, 'tipo': tipo})

        return resultado


class CriarouAtualizar:
    @staticmethod
    def _criar_cliente(empresa, nome, tipo_pessoa, documento, data_nascimento, nome_mae, estado_civil):
        cliente = Cliente(
            empresa=empresa,
            nome=nome,
            tipo_pessoa=tipo_pessoa,
            documento=documento,
            data_nascimento=data_nascimento,
            nome_mae=nome_mae,
            estado_civil=estado_civil,
        )
        cliente.full_clean(exclude=['rg', 'nome_pai'])
        cliente.save()



    @staticmethod
    def _atualizar_cliente(cliente, nome, nome_mae, data_nascimento, estado_civil):
        """
        Atualiza apenas os campos informativos do cliente.
        Não altera documento nem tipo_pessoa.
        """
        atualizado = False

        if nome and nome != cliente.nome:
            cliente.nome = nome
            atualizado = True
        if nome_mae and nome_mae != cliente.nome_mae:
            cliente.nome_mae = nome_mae
            atualizado = True
        if data_nascimento and data_nascimento != cliente.data_nascimento:
            cliente.data_nascimento = data_nascimento
            atualizado = True
        if not data_nascimento and data_nascimento != cliente.data_nascimento:
            cliente.data_nascimento = data_nascimento
            atualizado = True
        if estado_civil and estado_civil != cliente.estado_civil:
            cliente.estado_civil = estado_civil
            atualizado = True

        if atualizado:
            cliente.save(update_fields=['nome', 'nome_mae', 'data_nascimento', 'estado_civil'])


    @staticmethod
    def _adicionar_telefones(cliente, telefones):
        """
        Adiciona telefones que ainda não existem para o cliente.
        Respeita a UniqueConstraint (cliente, telefone).
        Diferentes tipos do mesmo número são aceitos pelo model (constraint é só no número).
        """
        numeros_existentes = set(
            Telefone.objects
            .filter(cliente=cliente)
            .values_list('telefone', flat=True)
        )

        novos = []
        vistos_neste_lote = set()  # evita duplicata dentro do próprio CSV

        for fone in telefones:
            numero = fone['numero']
            if numero in numeros_existentes or numero in vistos_neste_lote:
                continue
            novos.append(Telefone(
                cliente=cliente,
                telefone=numero,
                tipo=fone['tipo'],
                whats_app=False,
                ativo=True,
            ))
            vistos_neste_lote.add(numero)

        if novos:
            Telefone.objects.bulk_create(novos, ignore_conflicts=True)


    @staticmethod
    def _adicionar_emails(cliente, emails):
        """
        Adiciona e-mails que ainda não existem para o cliente.
        Respeita a UniqueConstraint (cliente, email, tipo).
        O mesmo endereço com tipo diferente é tratado como registro distinto.
        """
        existentes = set(
            Email.objects
            .filter(cliente=cliente)
            .values_list('email', 'tipo')
        )

        novos = []
        vistos_neste_lote = set()

        for item in emails:
            chave = (item['email'], item['tipo'])
            if chave in existentes or chave in vistos_neste_lote:
                continue
            novos.append(Email(
                cliente=cliente,
                email=item['email'],
                tipo=item['tipo'],
                ativo=True,
            ))
            vistos_neste_lote.add(chave)

        if novos:
            Email.objects.bulk_create(novos, ignore_conflicts=True)