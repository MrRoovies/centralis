from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import json
import re
from datetime import datetime
from apps.clientes.models import Cliente
from apps.clientes.services.importacao_service import Extrator, CriarouAtualizar

# ── Constantes ────────────────────────────────────────────────

ESTADOS_CIVIS_VALIDOS  = ['SOLTEIRO', 'CASADO', 'DIVORCIADO', 'VIUVO', 'UNIAO_ESTAVEL']

# Campos do cliente que podem ser atualizados no upsert
CAMPOS_UPSERT = ['nome', 'nome_mae', 'data_nascimento', 'estado_civil']


@login_required
@require_GET
def importar_clientes_view(request):
    """Renderiza a tela de importação via CSV."""
    return render(request, 'clientes/importar_clientes.html')


@login_required
@require_POST
def importar_csv(request):
    """
    Recebe um lote de registros (já parseados pelo front) e para cada um:
      - Se o documento não existe → cria cliente + telefones + e-mails.
      - Se o documento já existe e upsert=true → atualiza campos do cliente
        e adiciona telefones/e-mails novos sem remover os existentes.
      - Se o documento já existe e upsert=false → conta como duplicado e pula.

    Body esperado:
    {
        "clientes":    [ { "nome": ..., "documento": ..., "tipo_pessoa": ...,
                           "telefone1": ..., "telefone1_tipo": ...,
                           "email1": ..., "email1_tipo": ..., ... } ],
        "pular_erros": true,
        "upsert":      true
    }

    Retorna:
    {
        "criados":    N,
        "atualizados": N,
        "erros":      N,
        "log_erros":  [ { "documento": "...", "erro": "..." } ]
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'messages': {'importacao': {'__all__': ['JSON inválido']}}},
            status=400
        )

    registros    = data.get('clientes', [])
    pular_erros  = data.get('pular_erros', True)
    upsert       = data.get('upsert', True)
    empresa      = request.empresa

    if not registros:
        return JsonResponse(
            {'messages': {'importacao': {'__all__': ['Nenhum registro recebido.']}}},
            status=400
        )

    criados     = 0
    atualizados = 0
    erros       = 0
    log_erros   = []

    for registro in registros:
        documento_raw = re.sub(r'\D', '', str(registro.get('documento', '')))
        nome          = str(registro.get('nome', '')).strip()
        tipo_pessoa   = str(registro.get('tipo_pessoa', '')).upper().strip()

        # ── Validações mínimas (duplicam a validação do front como defesa) ──
        if not nome or not documento_raw or not tipo_pessoa:
            erros += 1
            log_erros.append({
                'documento': documento_raw or '?',
                'erro': 'Campos obrigatórios ausentes (nome, documento ou tipo_pessoa).'
            })
            if not pular_erros:
                break
            continue

        if tipo_pessoa not in ('PF', 'PJ'):
            erros += 1
            log_erros.append({
                'documento': documento_raw,
                'erro': f'tipo_pessoa inválido: "{tipo_pessoa}". Use PF ou PJ.'
            })
            if not pular_erros:
                break
            continue

        tamanho_esperado = 11 if tipo_pessoa == 'PF' else 14
        documento_raw = documento_raw.zfill(tamanho_esperado)

        # ── Dados opcionais do cliente ───────────────────────
        data_nascimento = _parse_data(registro.get('data_nascimento', ''))
        nome_mae = str(registro.get('nome_mae', '')).strip() or None

        estado_civil_raw = str(registro.get('estado_civil', '')).upper().strip()
        estado_civil = estado_civil_raw if estado_civil_raw in ESTADOS_CIVIS_VALIDOS else None

        # ── Telefones (1–3) ──────────────────────────────────
        telefones = Extrator._extrair_telefones(registro)

        # ── E-mails (1–3) ────────────────────────────────────
        emails = Extrator._extrair_emails(registro)

        # ── Verifica existência ──────────────────────────────
        cliente_existente = Cliente.objects.filter(
            empresa=empresa, documento=documento_raw
        ).first()

        if cliente_existente:
            if not upsert:
                # Pula silenciosamente — o front chama de "Atualizados" mas aqui são ignorados
                atualizados += 1
                continue

            # ── UPSERT: atualiza cliente e acrescenta contatos ──
            try:
                with transaction.atomic():
                    CriarouAtualizar._atualizar_cliente(
                        cliente_existente, nome, nome_mae, data_nascimento, estado_civil
                    )
                    CriarouAtualizar._adicionar_telefones(cliente_existente, telefones)
                    CriarouAtualizar._adicionar_emails(cliente_existente, emails)
                atualizados += 1

            except Exception as e:
                erros += 1
                log_erros.append({'documento': documento_raw, 'erro': _msg_erro(e)})
                if not pular_erros:
                    break

        else:
            # ── CRIAÇÃO ──────────────────────────────────────
            try:
                with transaction.atomic():
                    CriarouAtualizar._criar_cliente(
                        empresa, nome, tipo_pessoa, documento_raw,
                        data_nascimento, nome_mae, estado_civil
                    )

                    CriarouAtualizar._adicionar_telefones(cliente, telefones)
                    CriarouAtualizar._adicionar_emails(cliente, emails)

                criados += 1

            except (ValidationError, IntegrityError) as e:
                erros += 1
                log_erros.append({'documento': documento_raw, 'erro': _msg_erro(e)})
                if not pular_erros:
                    break

            except Exception as e:
                erros += 1
                log_erros.append({'documento': documento_raw, 'erro': str(e)})
                if not pular_erros:
                    break

    return JsonResponse({
        'criados':     criados,
        'atualizados': atualizados,
        'erros':       erros,
        'log_erros':   log_erros,
    }, status=200)


# ════════════════════════════════════════════════════════════
# Helpers privados
# ════════════════════════════════════════════════════════════

def _parse_data(valor):
    """Converte string DD/MM/AAAA ou AAAA-MM-DD para date. Retorna None se inválido."""
    valor = str(valor).strip()
    if not valor:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(valor, fmt).date()
        except ValueError:
            continue
    return None


def _msg_erro(exc):
    """Formata ValidationError e outros em string legível."""
    if hasattr(exc, 'message_dict'):
        return '; '.join(
            f"{campo}: {', '.join(msgs)}"
            for campo, msgs in exc.message_dict.items()
        )
    return str(exc)