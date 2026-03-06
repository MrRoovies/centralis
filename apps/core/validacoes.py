import re

class Validar():
    def valida_Fone(self, telefone):
        if not re.match(r'^[1-9]{2}(?:9\d{8}|[2-8]\d{7})$', telefone):
            return False
        return True
