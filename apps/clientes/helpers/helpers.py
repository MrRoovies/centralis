from apps.clientes.models import Vinculo, Cliente
from decimal import Decimal, InvalidOperation
from datetime import datetime

def _parse_data(valor):
    valor = str(valor).strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(valor, fmt).date()
        except ValueError:
            continue
    return None

def _msg_erro(exc):
    if hasattr(exc, 'message_dict'):
        return '; '.join(
            f"{campo}: {', '.join(msgs)}"
            for campo, msgs in exc.message_dict.items()
        )
    return str(exc)

def _decimal(valor):
    if not valor:
        return None
    try:
        return Decimal(str(valor).replace(',', '.').strip())
    except InvalidOperation:
        return None
 
 
def _inteiro(valor):
    try:
        return int(str(valor).strip())
    except (ValueError, TypeError):
        return None
 
 
def _msg(exc):
    if hasattr(exc, 'message_dict'):
        return '; '.join(f"{c}: {', '.join(m)}" for c, m in exc.message_dict.items())
    return str(exc)
 
 
def _achar_cliente(empresa, documento_raw):
    """Tenta localizar cliente com CPF (11) ou CNPJ (14)."""
    for tam in (11, 14):
        doc = documento_raw.zfill(tam)
        cli = Cliente.objects.filter(empresa=empresa, documento=doc).first()
        if cli:
            return cli
    return None
 
 
def _achar_vinculo(empresa, cliente, matricula):
    return Vinculo.objects.filter(
        empresa=empresa,
        cliente=cliente,
        matricula=matricula,
    ).first()
 