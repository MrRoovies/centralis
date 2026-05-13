import re
from apps.clientes.models import Cliente, Telefone, Email

class Extrator:
    @staticmethod
    def _extrair_telefones(registro):
        TIPOS_TELEFONE_VALIDOS = ['FIXO', 'CELULAR', 'CORPORATIVO']
        resultado = []
        for i in range(1, 4):
            numero = re.sub(r'\D', '', str(registro.get(f'telefone{i}', '')))
            tipo = str(registro.get(f'telefone{i}_tipo', '')).upper().strip()
            if not numero:
                continue
            if len(numero) not in (10, 11):
                continue
            if tipo not in TIPOS_TELEFONE_VALIDOS:
                tipo = 'CELULAR' if len(numero) == 11 else 'FIXO'
            resultado.append({'numero': numero, 'tipo': tipo})
        return resultado

    @staticmethod
    def _extrair_emails(registro):
        TIPOS_EMAIL_VALIDOS = ['PESSOAL', 'CORPORATIVO']
        resultado = []
        for i in range(1, 4):
            mail = str(registro.get(f'email{i}', '')).strip()
            tipo = str(registro.get(f'email{i}_tipo', '')).upper().strip()
            if not mail:
                continue
            if '@' not in mail or '.' not in mail.split('@')[-1]:
                continue
            if tipo not in TIPOS_EMAIL_VALIDOS:
                tipo = 'PESSOAL'
            resultado.append({'email': mail, 'tipo': tipo})
        return resultado

    @staticmethod
    def _extrair_dados_bancarios(registro):
        """
        Lê banco1_cod/banco1_agencia/banco1_conta, banco2_..., banco3_...
        Retorna lista de dicts válidos:
        [{'cod_banco': '...', 'agencia': '...', 'conta': '...'}]
        """
        resultado = []
        for i in range(1, 4):
            cod    = str(registro.get(f'banco{i}_cod',     '')).strip()
            agencia = str(registro.get(f'banco{i}_agencia', '')).strip()
            conta   = str(registro.get(f'banco{i}_conta',   '')).strip()

            if not cod or not agencia or not conta:
                continue

            resultado.append({
                'cod_banco': cod,
                'agencia':   agencia,
                'conta':     conta,
            })
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
        return cliente

    @staticmethod
    def _atualizar_cliente(cliente, nome, nome_mae, data_nascimento, estado_civil):
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
        numeros_existentes = set(
            Telefone.objects
            .filter(cliente=cliente)
            .values_list('telefone', flat=True)
        )
        novos = []
        vistos = set()
        for fone in telefones:
            numero = fone['numero']
            if numero in numeros_existentes or numero in vistos:
                continue
            novos.append(Telefone(
                cliente=cliente,
                telefone=numero,
                tipo=fone['tipo'],
                whats_app=False,
                ativo=True,
            ))
            vistos.add(numero)
        if novos:
            Telefone.objects.bulk_create(novos, ignore_conflicts=True)

    @staticmethod
    def _adicionar_emails(cliente, emails):
        existentes = set(
            Email.objects
            .filter(cliente=cliente)
            .values_list('email', 'tipo')
        )
        novos = []
        vistos = set()
        for item in emails:
            chave = (item['email'], item['tipo'])
            if chave in existentes or chave in vistos:
                continue
            novos.append(Email(
                cliente=cliente,
                email=item['email'],
                tipo=item['tipo'],
                ativo=True,
            ))
            vistos.add(chave)
        if novos:
            Email.objects.bulk_create(novos, ignore_conflicts=True)

    @staticmethod
    def _adicionar_dados_bancarios(cliente, empresa, dados_bancarios):
        """
        Adiciona dados bancários que ainda não existem para o cliente.
        Busca o banco pelo cod_banco; ignora silenciosamente se não encontrado.
        Respeita a UniqueConstraint (empresa, cliente, banco, agencia, conta).
        """
        from apps.clientes.models import DadosBancarios, Bancos

        if not dados_bancarios:
            return

        existentes = set(
            DadosBancarios.objects
            .filter(cliente=cliente, empresa=empresa)
            .values_list('banco_id', 'agencia', 'conta')
        )

        novos = []
        vistos = set()

        for item in dados_bancarios:
            banco = Bancos.objects.filter(cod_banco=item['cod_banco']).first()
            if not banco:
                continue  # banco desconhecido — ignora silenciosamente

            agencia = item['agencia'].strip().zfill(4)
            conta   = item['conta'].strip()

            chave = (banco.id, agencia, conta)
            if chave in existentes or chave in vistos:
                continue

            novos.append(DadosBancarios(
                cliente=cliente,
                banco=banco,
                agencia=agencia,
                conta=conta,
                empresa=empresa,
            ))
            vistos.add(chave)

        if novos:
            DadosBancarios.objects.bulk_create(novos, ignore_conflicts=True)