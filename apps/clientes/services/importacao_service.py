import re


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