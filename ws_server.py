"""
Servidor WebSocket em Python puro (asyncio, SÓ biblioteca padrão).
Implementa o protocolo RFC 6455: handshake, frames (texto/binário, máscara,
fragmentação), ping/pong, close.

Rodar:
    export WS_SECRET="um-segredo-grande-e-aleatorio"
    python ws_server.py

Variáveis de ambiente:
    WS_SECRET           (obrigatório) assina os tokens e protege o endpoint de push
    WS_HOST             padrão 0.0.0.0
    WS_PORT             padrão 8765   (WebSocket dos navegadores)
    WS_CONTROL_PORT     padrão 8766   (push interno, escuta só em 127.0.0.1)
    WS_ALLOWED_ORIGINS  lista separada por vírgula, ex.: https://crm.meusite.com
                        (vazio = não verifica Origin)
    WS_CERT / WS_KEY    opcional: habilita TLS (wss://) direto no servidor
                        (alternativa: terminar TLS num proxy como Nginx)

Como funciona:
    Navegador  --ws://host:8765/ws?token=...-->  este servidor
    Backend    --POST http://127.0.0.1:8766/enviar-->  este servidor  --> navegadores
    (o backend usa ws_push.enviar(...), que faz esse POST)

Protocolo das mensagens (JSON texto): {"tipo": "...", "dados": {...}}
Cada usuário entra automaticamente no grupo "user_<id>".
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import ssl
import struct
import time
from urllib.parse import parse_qs, urlsplit

from ws_push import validar_token

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"  # constante da RFC 6455

HOST = os.environ.get("WS_HOST", "0.0.0.0")
PORT = int(os.environ.get("WS_PORT", "8765"))
CONTROL_PORT = int(os.environ.get("WS_CONTROL_PORT", "8766"))
SECRET = os.environ.get("WS_SECRET", "")
ORIGENS = [o.strip() for o in os.environ.get("WS_ALLOWED_ORIGINS", "").split(",") if o.strip()]

MAX_MSG = 1_048_576      # 1 MB por mensagem
PING_INTERVALO = 30      # segundos entre pings do servidor
TIMEOUT_INATIVO = 90     # sem nenhum frame por este tempo -> derruba

OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA

log = logging.getLogger("ws")


# ──────────────────────────────────────────────────────────────
# Estado: conexões e grupos
# ──────────────────────────────────────────────────────────────
class Conexao:
    def __init__(self, reader, writer, user_id):
        self.reader = reader
        self.writer = writer
        self.user_id = user_id
        self.grupos = set()
        self.lock = asyncio.Lock()          # evita frames intercalados na escrita
        self.ultima_atividade = time.monotonic()
        self.fechada = False


GRUPOS = {}  # nome -> set[Conexao]


def entrar(conn, grupo):
    GRUPOS.setdefault(grupo, set()).add(conn)
    conn.grupos.add(grupo)


def sair_de_todos(conn):
    for g in conn.grupos:
        membros = GRUPOS.get(g)
        if membros:
            membros.discard(conn)
            if not membros:
                GRUPOS.pop(g, None)
    conn.grupos.clear()


# ──────────────────────────────────────────────────────────────
# Frames (RFC 6455)
# ──────────────────────────────────────────────────────────────
class ErroProtocolo(Exception):
    def __init__(self, codigo, motivo=""):
        super().__init__(motivo)
        self.codigo = codigo
        self.motivo = motivo


def desmascarar(dados: bytes, mascara: bytes) -> bytes:
    n = len(dados)
    if n == 0:
        return b""
    chave = (mascara * (n // 4 + 1))[:n]
    return (int.from_bytes(dados, "big") ^ int.from_bytes(chave, "big")).to_bytes(n, "big")


def montar_frame(opcode: int, payload: bytes = b"") -> bytes:
    """Frame servidor->cliente (nunca mascarado)."""
    n = len(payload)
    cab = bytearray([0x80 | opcode])  # FIN=1
    if n < 126:
        cab.append(n)
    elif n < 65536:
        cab.append(126)
        cab += struct.pack("!H", n)
    else:
        cab.append(127)
        cab += struct.pack("!Q", n)
    return bytes(cab) + payload


async def ler_frame(reader):
    b1, b2 = await reader.readexactly(2)
    fin = bool(b1 & 0x80)
    opcode = b1 & 0x0F
    mascarado = bool(b2 & 0x80)
    n = b2 & 0x7F

    if b1 & 0x70:
        raise ErroProtocolo(1002, "bits RSV não suportados")
    if n == 126:
        n = struct.unpack("!H", await reader.readexactly(2))[0]
    elif n == 127:
        n = struct.unpack("!Q", await reader.readexactly(8))[0]

    if not mascarado:
        raise ErroProtocolo(1002, "cliente deve mascarar os frames")
    if opcode >= 0x8 and (n > 125 or not fin):
        raise ErroProtocolo(1002, "frame de controle inválido")
    if n > MAX_MSG:
        raise ErroProtocolo(1009, "mensagem grande demais")

    mascara = await reader.readexactly(4)
    dados = await reader.readexactly(n) if n else b""
    return fin, opcode, desmascarar(dados, mascara)


async def enviar_frame(conn, opcode, payload=b""):
    if conn.fechada:
        return
    try:
        async with conn.lock:
            conn.writer.write(montar_frame(opcode, payload))
            await conn.writer.drain()
    except (ConnectionError, OSError):
        conn.fechada = True


async def enviar_texto(conn, obj):
    await enviar_frame(conn, OP_TEXT, json.dumps(obj, ensure_ascii=False).encode())


async def fechar(conn, codigo=1000, motivo=""):
    if conn and not conn.fechada:
        await enviar_frame(conn, OP_CLOSE, struct.pack("!H", codigo) + motivo.encode()[:120])
        conn.fechada = True


async def ler_mensagem(conn):
    """
    Lê uma mensagem de dados completa (juntando fragmentos) e trata
    ping/pong/close no caminho. Retorna (opcode, bytes) ou None se fechou.
    """
    buffer = bytearray()
    op_inicial = None
    while True:
        fin, op, dados = await ler_frame(conn.reader)
        conn.ultima_atividade = time.monotonic()

        if op == OP_PING:
            await enviar_frame(conn, OP_PONG, dados)
            continue
        if op == OP_PONG:
            continue
        if op == OP_CLOSE:
            await enviar_frame(conn, OP_CLOSE, dados[:2])  # devolve o código recebido
            conn.fechada = True
            return None

        if op in (OP_TEXT, OP_BIN):
            if op_inicial is not None:
                raise ErroProtocolo(1002, "nova mensagem no meio de uma fragmentada")
            op_inicial, buffer = op, bytearray(dados)
        elif op == OP_CONT:
            if op_inicial is None:
                raise ErroProtocolo(1002, "continuação sem início")
            buffer += dados
        else:
            raise ErroProtocolo(1002, "opcode desconhecido")

        if len(buffer) > MAX_MSG:
            raise ErroProtocolo(1009, "mensagem grande demais")
        if fin:
            return op_inicial, bytes(buffer)


# ──────────────────────────────────────────────────────────────
# HTTP mínimo (handshake e endpoint de push)
# ──────────────────────────────────────────────────────────────
async def ler_requisicao_http(reader):
    bruto = await reader.readuntil(b"\r\n\r\n")
    linhas = bruto.decode("latin-1").split("\r\n")
    metodo, alvo, _ = linhas[0].split(" ", 2)
    headers = {}
    for linha in linhas[1:]:
        if ":" in linha:
            k, v = linha.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return metodo, alvo, headers


async def responder_http(writer, status, texto, tipo="text/plain; charset=utf-8"):
    corpo = texto.encode()
    writer.write(
        (f"HTTP/1.1 {status}\r\nContent-Type: {tipo}\r\n"
         f"Content-Length: {len(corpo)}\r\nConnection: close\r\n\r\n").encode() + corpo
    )
    await writer.drain()


# ──────────────────────────────────────────────────────────────
# Seu código entra aqui
# ──────────────────────────────────────────────────────────────
async def ao_receber(conn, tipo, dados):
    """
    Chamado a cada mensagem JSON vinda do navegador (exceto "ping").
    Personalize: entrar em grupos, repassar para outros usuários etc.
    Exemplo:
        if tipo == "entrar_grupo":
            entrar(conn, f"empresa_{dados['id']}")   # valide permissão antes!
    """
    log.debug("recebido de user %s: %s %s", conn.user_id, tipo, dados)


async def transmitir(grupo, tipo, dados=None) -> int:
    """Envia {"tipo","dados"} para todos do grupo. Retorna quantos receberam."""
    conns = list(GRUPOS.get(grupo, ()))
    msg = json.dumps({"tipo": tipo, "dados": dados or {}}, ensure_ascii=False).encode()
    await asyncio.gather(*(enviar_frame(c, OP_TEXT, msg) for c in conns))
    return len(conns)


# ──────────────────────────────────────────────────────────────
# Servidor WebSocket (navegadores)
# ──────────────────────────────────────────────────────────────
async def batimento(conn):
    while True:
        await asyncio.sleep(PING_INTERVALO)
        if time.monotonic() - conn.ultima_atividade > TIMEOUT_INATIVO:
            await fechar(conn, 1001, "inativo")
            conn.writer.close()
            return
        await enviar_frame(conn, OP_PING, b"")


async def tratar_cliente(reader, writer):
    conn = None
    tarefa_batimento = None
    try:
        metodo, alvo, h = await asyncio.wait_for(ler_requisicao_http(reader), 10)
        partes = urlsplit(alvo)

        if partes.path != "/ws":
            return await responder_http(writer, "404 Not Found", "use /ws")
        if (metodo != "GET" or h.get("upgrade", "").lower() != "websocket"
                or "upgrade" not in h.get("connection", "").lower()
                or h.get("sec-websocket-version") != "13"
                or not h.get("sec-websocket-key")):
            return await responder_http(writer, "400 Bad Request", "handshake inválido")
        if ORIGENS and h.get("origin") not in ORIGENS:
            log.warning("handshake recusado (403): origem não permitida: %s", h.get("origin"))
            return await responder_http(writer, "403 Forbidden", "origem não permitida")

        user_id = validar_token(parse_qs(partes.query).get("token", [""])[0])
        if user_id is None:
            log.warning("handshake recusado (401): token inválido ou expirado. "
                        "Se acontece com todos os usuários, o WS_SECRET do Django "
                        "é diferente do deste servidor.")
            return await responder_http(writer, "401 Unauthorized", "token inválido ou expirado")

        aceita = base64.b64encode(
            hashlib.sha1((h["sec-websocket-key"] + GUID).encode()).digest()
        ).decode()
        writer.write(
            ("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
             f"Connection: Upgrade\r\nSec-WebSocket-Accept: {aceita}\r\n\r\n").encode()
        )
        await writer.drain()

        conn = Conexao(reader, writer, user_id)
        entrar(conn, f"user_{user_id}")
        log.info("user %s conectado (%d grupos ativos)", user_id, len(GRUPOS))
        await enviar_texto(conn, {"tipo": "conectado", "dados": {"user_id": user_id}})
        tarefa_batimento = asyncio.create_task(batimento(conn))

        while True:
            msg = await ler_mensagem(conn)
            if msg is None:
                break
            op, dados = msg
            if op != OP_TEXT:
                continue
            try:
                obj = json.loads(dados.decode("utf-8"))
            except UnicodeDecodeError:
                raise ErroProtocolo(1007, "texto não é UTF-8 válido")
            except ValueError:
                continue  # JSON inválido: ignora
            if not isinstance(obj, dict):
                continue
            if obj.get("tipo") == "ping":
                await enviar_texto(conn, {"tipo": "pong"})
                continue
            try:
                await ao_receber(conn, obj.get("tipo"), obj.get("dados"))
            except Exception:
                log.exception("erro em ao_receber")

    except ErroProtocolo as e:
        await fechar(conn, e.codigo, e.motivo)
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError,
            asyncio.TimeoutError, ConnectionError, OSError):
        pass
    except Exception:
        log.exception("erro inesperado na conexão")
    finally:
        if tarefa_batimento:
            tarefa_batimento.cancel()
        if conn:
            sair_de_todos(conn)
            log.info("user %s desconectado", conn.user_id)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
# Endpoint de controle (push do backend) — só 127.0.0.1
# ──────────────────────────────────────────────────────────────
async def tratar_controle(reader, writer):
    try:
        metodo, alvo, h = await asyncio.wait_for(ler_requisicao_http(reader), 10)
        if metodo != "POST" or urlsplit(alvo).path != "/enviar":
            return await responder_http(writer, "404 Not Found", "use POST /enviar")
        if not hmac.compare_digest(h.get("x-token", "").encode(), SECRET.encode()):
            return await responder_http(writer, "401 Unauthorized", "token inválido")

        tamanho = int(h.get("content-length", "0"))
        if not 0 < tamanho <= MAX_MSG:
            return await responder_http(writer, "400 Bad Request", "corpo inválido")
        corpo = json.loads(await asyncio.wait_for(reader.readexactly(tamanho), 10))

        grupo = corpo.get("grupo")
        if grupo is None and "user_id" in corpo:
            grupo = f"user_{corpo['user_id']}"
        if grupo is None:
            return await responder_http(writer, "400 Bad Request", "informe grupo ou user_id")

        n = await transmitir(grupo, corpo["tipo"], corpo.get("dados"))
        await responder_http(writer, "200 OK", json.dumps({"entregues": n}), "application/json")

    except (KeyError, ValueError, TypeError, AttributeError):
        try:
            await responder_http(writer, "400 Bad Request", "requisição inválida")
        except Exception:
            pass
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError,
            asyncio.TimeoutError, ConnectionError, OSError):
        pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
async def main():
    if not SECRET:
        raise SystemExit("Defina WS_SECRET antes de iniciar o servidor.")
    if not ORIGENS:
        log.warning("WS_ALLOWED_ORIGINS vazio: o cabeçalho Origin NÃO está sendo verificado.")

    contexto_ssl = None
    cert, chave = os.environ.get("WS_CERT"), os.environ.get("WS_KEY")
    if cert and chave:
        contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto_ssl.load_cert_chain(cert, chave)

    srv = await asyncio.start_server(tratar_cliente, HOST, PORT, ssl=contexto_ssl)
    ctrl = await asyncio.start_server(tratar_controle, "127.0.0.1", CONTROL_PORT)
    esquema = "wss" if contexto_ssl else "ws"
    log.info("WebSocket em %s://%s:%d/ws | controle em 127.0.0.1:%d", esquema, HOST, PORT, CONTROL_PORT)

    async with srv, ctrl:
        await asyncio.gather(srv.serve_forever(), ctrl.serve_forever())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass