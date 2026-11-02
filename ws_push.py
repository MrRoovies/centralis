"""
Utilitários para falar com o servidor WebSocket (ws_server.py).
Só biblioteca padrão — pode ser importado de qualquer projeto
(Django, script, cron, listener...).

Variáveis de ambiente (as mesmas do servidor):
    WS_SECRET        segredo compartilhado (obrigatório)
    WS_CONTROL_PORT  porta de controle do servidor (padrão 8766)

1) Dar um token ao navegador (quem autentica o usuário gera o token):

    from ws_push import gerar_token
    token = gerar_token(user_id=request.user.id, ttl=3600)
    # devolva ao JS (ex.: JsonResponse({"token": token}))

2) Enviar uma mensagem de qualquer lugar do backend:

    from ws_push import enviar
    enviar("chamada_atendida", {"cliente_id": 12}, user_id=5)
    enviar("aviso", {"texto": "Fila reiniciada"}, grupo="empresa_3")
"""

import base64
import hashlib
import hmac
import http.client
import json
import os
import time


def _segredo() -> bytes:
    segredo = os.environ.get("WS_SECRET", "")
    if not segredo:
        raise RuntimeError("Defina a variável de ambiente WS_SECRET.")
    return segredo.encode()


def _b64(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).decode().rstrip("=")


def _b64_decode(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def gerar_token(user_id, ttl: int = 3600) -> str:
    """Token assinado (HMAC-SHA256) com o id do usuário e validade."""
    payload = json.dumps(
        {"uid": user_id, "exp": int(time.time()) + ttl}, separators=(",", ":")
    ).encode()
    corpo = _b64(payload)
    assinatura = hmac.new(_segredo(), corpo.encode(), hashlib.sha256).hexdigest()
    return f"{corpo}.{assinatura}"


def validar_token(token: str):
    """Retorna o user_id se o token for válido e não expirado; senão None."""
    try:
        corpo, assinatura = token.split(".", 1)
        esperada = hmac.new(_segredo(), corpo.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(assinatura, esperada):
            return None
        payload = json.loads(_b64_decode(corpo))
        if payload["exp"] < time.time():
            return None
        return payload["uid"]
    except (ValueError, KeyError, TypeError):
        return None


def enviar(tipo, dados=None, *, grupo=None, user_id=None,
           host="127.0.0.1", porta=None, timeout=5) -> int:
    """
    Pede ao servidor para entregar {"tipo", "dados"} a um grupo ou usuário.
    Retorna quantas conexões receberam. Levanta exceção se falhar.
    """
    if grupo is None and user_id is None:
        raise ValueError("Informe grupo= ou user_id=.")

    porta = porta or int(os.environ.get("WS_CONTROL_PORT", "8766"))
    corpo = {"tipo": tipo, "dados": dados or {}}
    if grupo is not None:
        corpo["grupo"] = grupo
    else:
        corpo["user_id"] = user_id

    conn = http.client.HTTPConnection(host, porta, timeout=timeout)
    try:
        conn.request(
            "POST", "/enviar",
            json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
            {"Content-Type": "application/json", "X-Token": _segredo().decode()},
        )
        resp = conn.getresponse()
        texto = resp.read().decode()
        if resp.status != 200:
            raise RuntimeError(f"Servidor WS respondeu {resp.status}: {texto}")
        return json.loads(texto)["entregues"]
    finally:
        conn.close()
