from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import json
import re
from apps.clientes.models import Cliente, Vinculo, Financeiro, Divida, Veiculo
from apps.clientes.services.importacao_service import Extrator, CriarouAtualizar
from apps.clientes.helpers.helpers import (
    _parse_data, _msg_erro, _decimal, 
    _inteiro, _msg, _achar_cliente, 
    _achar_vinculo)

ESTADOS_CIVIS_VALIDOS = ['SOLTEIRO', 'CASADO', 'DIVORCIADO', 'VIUVO', 'UNIAO_ESTAVEL']
CAMPOS_UPSERT = ['nome', 'nome_mae', 'data_nascimento', 'estado_civil']
CHOICE_CAT_VALIDOS = {'CARROS', 'MOTO', 'CAMINHOES'}


@login_required
@require_GET
def importar_clientes_view(request):
    return render(request, 'clientes/importar_clientes.html')


@login_required
@require_POST
def importar_csv(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'messages': {'importacao': {'__all__': ['JSON inválido']}}},
            status=400
        )

    registros   = data.get('clientes', [])
    pular_erros = data.get('pular_erros', True)
    upsert      = data.get('upsert', True)
    empresa     = request.empresa

    if not registros:
        return JsonResponse(
            {'messages': {'importacao': {'__all__': ['Nenhum registro recebido.']}}},
            status=400
        )

    criados = 0; atualizados = 0; erros = 0
    log_erros = []

    for registro in registros:
        documento_raw = re.sub(r'\D', '', str(registro.get('documento', '')))
        nome          = str(registro.get('nome', '')).strip()
        tipo_pessoa   = str(registro.get('tipo_pessoa', '')).upper().strip()

        if not nome or not documento_raw or not tipo_pessoa:
            erros += 1
            log_erros.append({
                'documento': documento_raw or '?',
                'erro': 'Campos obrigatórios ausentes (nome, documento ou tipo_pessoa).'
            })
            if not pular_erros: break
            continue

        if tipo_pessoa not in ('PF', 'PJ'):
            erros += 1
            log_erros.append({
                'documento': documento_raw,
                'erro': f'tipo_pessoa inválido: "{tipo_pessoa}". Use PF ou PJ.'
            })
            if not pular_erros: break
            continue

        tamanho_esperado = 11 if tipo_pessoa == 'PF' else 14
        documento_raw = documento_raw.zfill(tamanho_esperado)

        data_nascimento   = _parse_data(registro.get('data_nascimento', ''))
        nome_mae          = str(registro.get('nome_mae', '')).strip() or None
        estado_civil_raw  = str(registro.get('estado_civil', '')).upper().strip()
        estado_civil      = estado_civil_raw if estado_civil_raw in ESTADOS_CIVIS_VALIDOS else None

        telefones        = Extrator._extrair_telefones(registro)
        emails           = Extrator._extrair_emails(registro)
        dados_bancarios  = Extrator._extrair_dados_bancarios(registro)  # ← novo

        cliente_existente = Cliente.objects.filter(
            empresa=empresa, documento=documento_raw
        ).first()

        if cliente_existente:
            if not upsert:
                atualizados += 1
                continue
            try:
                with transaction.atomic():
                    CriarouAtualizar._atualizar_cliente(
                        cliente_existente, nome, nome_mae, data_nascimento, estado_civil
                    )
                    CriarouAtualizar._adicionar_telefones(cliente_existente, telefones)
                    CriarouAtualizar._adicionar_emails(cliente_existente, emails)
                    CriarouAtualizar._adicionar_dados_bancarios(  # ← novo
                        cliente_existente, empresa, dados_bancarios
                    )
                atualizados += 1
            except Exception as e:
                erros += 1
                log_erros.append({'documento': documento_raw, 'erro': _msg_erro(e)})
                if not pular_erros: break
        else:
            try:
                with transaction.atomic():
                    cliente = CriarouAtualizar._criar_cliente(
                        empresa, nome, tipo_pessoa, documento_raw,
                        data_nascimento, nome_mae, estado_civil
                    )
                    CriarouAtualizar._adicionar_telefones(cliente, telefones)
                    CriarouAtualizar._adicionar_emails(cliente, emails)
                    CriarouAtualizar._adicionar_dados_bancarios(  # ← novo
                        cliente, empresa, dados_bancarios
                    )
                criados += 1
            except (ValidationError, IntegrityError) as e:
                erros += 1
                log_erros.append({'documento': documento_raw, 'erro': _msg_erro(e)})
                if not pular_erros: break
            except Exception as e:
                erros += 1
                log_erros.append({'documento': documento_raw, 'erro': str(e)})
                if not pular_erros: break

    return JsonResponse({
        'criados':     criados,
        'atualizados': atualizados,
        'erros':       erros,
        'log_erros':   log_erros,
    }, status=200)

 
# ─── VIEW: Vínculo ───────────────────────────────────────────
 
@login_required
@require_POST
def importar_vinculo_csv(request):
    """
    Payload: { "registros": [...], "pular_erros": true }
 
    Colunas CSV:
        documento (obrig), matricula (obrig),
        convenio, orgao, instituidor, sit_func  (todos opcionais)
 
    Lógica:  get_or_create por (empresa, cliente, matricula).
             Se existir → atualiza convenio/orgao/sit_func/instituidor se fornecidos.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'messages': {'importacao': {'__all__': ['JSON inválido']}}}, status=400)
 
    registros   = data.get('registros', [])
    pular_erros = data.get('pular_erros', True)
    empresa     = request.empresa
 
    if not registros:
        return JsonResponse({'messages': {'importacao': {'__all__': ['Nenhum registro recebido.']}}}, status=400)
 
    criados = 0; atualizados = 0; erros = 0; log_erros = []
 
    for reg in registros:
        doc_raw  = re.sub(r'\D', '', str(reg.get('documento', '')))
        matricula = str(reg.get('matricula', '')).strip()
 
        if not doc_raw or not matricula:
            erros += 1
            log_erros.append({'documento': doc_raw or '?', 'erro': 'documento e matricula são obrigatórios.'})
            if not pular_erros: break
            continue
 
        cliente = _achar_cliente(empresa, doc_raw)
        if not cliente:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': 'Cliente não encontrado. Importe o cadastro primeiro.'})
            if not pular_erros: break
            continue
 
        convenio    = str(reg.get('convenio',    '') or '').strip() or None
        orgao       = str(reg.get('orgao',       '') or '').strip() or None
        sit_func    = str(reg.get('sit_func',    '') or '').strip() or None
        instituidor = str(reg.get('instituidor', '') or '').strip() or None
 
        # Normalização SIAPE
        if convenio and convenio.upper() == 'SIAPE':
            matricula = matricula.zfill(7)
            if instituidor:
                instituidor = instituidor.zfill(8)
 
        try:
            with transaction.atomic():
                vinculo, criado = Vinculo.objects.get_or_create(
                    empresa=empresa,
                    cliente=cliente,
                    matricula=matricula,
                    defaults={
                        'convenio':    convenio,
                        'orgao':       orgao,
                        'sit_func':    sit_func,
                        'instituidor': instituidor,
                    }
                )
                if not criado:
                    mudou = False
                    for campo, val in [('convenio', convenio), ('orgao', orgao),
                                       ('sit_func', sit_func), ('instituidor', instituidor)]:
                        if val and getattr(vinculo, campo) != val:
                            setattr(vinculo, campo, val)
                            mudou = True
                    if mudou:
                        vinculo.save()
 
            if criado:
                criados += 1
            else:
                atualizados += 1
 
        except (ValidationError, IntegrityError) as exc:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': _msg(exc)})
            if not pular_erros: break
        except Exception as exc:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': str(exc)})
            if not pular_erros: break
 
    return JsonResponse({'criados': criados, 'atualizados': atualizados,
                         'erros': erros, 'log_erros': log_erros})
 
 
# ─── VIEW: Financeiro ────────────────────────────────────────
 
@login_required
@require_POST
def importar_financeiro_csv(request):
    """
    Payload: { "registros": [...], "pular_erros": true }
 
    Colunas CSV (todas obrigatórias):
        documento, matricula, referencia,
        salario, margem_consig, margem_ct, margem_ct_bn
 
    Lógica: update_or_create por (empresa, vinculo, referencia).
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'messages': {'importacao': {'__all__': ['JSON inválido']}}}, status=400)
 
    registros   = data.get('registros', [])
    pular_erros = data.get('pular_erros', True)
    empresa     = request.empresa
 
    if not registros:
        return JsonResponse({'messages': {'importacao': {'__all__': ['Nenhum registro recebido.']}}}, status=400)
 
    OBRIG = ['documento', 'matricula', 'referencia', 'salario', 'margem_consig', 'margem_ct', 'margem_ct_bn']
 
    criados = 0; atualizados = 0; erros = 0; log_erros = []
 
    for reg in registros:
        doc_raw   = re.sub(r'\D', '', str(reg.get('documento', '')))
        matricula = str(reg.get('matricula', '')).strip()
        ref_raw   = str(reg.get('referencia', '')).strip()
 
        falta = [f for f in OBRIG if not str(reg.get(f, '')).strip()]
        if falta:
            erros += 1
            log_erros.append({'documento': doc_raw or '?', 'erro': f'Campos obrigatórios vazios: {", ".join(falta)}'})
            if not pular_erros: break
            continue
 
        referencia = _parse_data(ref_raw)
        if not referencia:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': f'Data de referência inválida: "{ref_raw}"'})
            if not pular_erros: break
            continue
 
        salario       = _decimal(reg.get('salario'))
        margem_consig = _decimal(reg.get('margem_consig'))
        margem_ct     = _decimal(reg.get('margem_ct'))
        margem_ct_bn  = _decimal(reg.get('margem_ct_bn'))
 
        if any(v is None for v in [salario, margem_consig, margem_ct, margem_ct_bn]):
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': 'Valores numéricos inválidos nos campos de margem/salário.'})
            if not pular_erros: break
            continue
 
        cliente = _achar_cliente(empresa, doc_raw)
        if not cliente:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': 'Cliente não encontrado.'})
            if not pular_erros: break
            continue
 
        vinculo = _achar_vinculo(empresa, cliente, matricula)
        if not vinculo:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': f'Vínculo com matrícula "{matricula}" não encontrado. Importe os vínculos primeiro.'})
            if not pular_erros: break
            continue
 
        try:
            with transaction.atomic():
                _, criado = Financeiro.objects.update_or_create(
                    empresa=empresa,
                    vinculo=vinculo,
                    referencia=referencia,
                    defaults={
                        'salario':       salario,
                        'margem_consig': margem_consig,
                        'margem_ct':     margem_ct,
                        'margem_ct_bn':  margem_ct_bn,
                    }
                )
            if criado: criados += 1
            else:      atualizados += 1
 
        except (ValidationError, IntegrityError) as exc:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': _msg(exc)})
            if not pular_erros: break
        except Exception as exc:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': str(exc)})
            if not pular_erros: break
 
    return JsonResponse({'criados': criados, 'atualizados': atualizados,
                         'erros': erros, 'log_erros': log_erros})
 
 
# ─── VIEW: Dívidas ───────────────────────────────────────────
 
@login_required
@require_POST
def importar_dividas_csv(request):
    """
    Payload: { "registros": [...], "pular_erros": true }
 
    Colunas CSV:
        obrigatórios: documento, matricula, referencia,
                      saldo_devedor, prazo_faltante, parcela, taxa
        opcionais:    banco, rubrica, tipo, contrato
 
    Cada linha é uma dívida independente.
    Lógica: update_or_create por (empresa, vinculo, contrato, referencia).
            Se contrato estiver vazio → sempre cria (sem upsert).
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'messages': {'importacao': {'__all__': ['JSON inválido']}}}, status=400)
 
    registros   = data.get('registros', [])
    pular_erros = data.get('pular_erros', True)
    empresa     = request.empresa
 
    if not registros:
        return JsonResponse({'messages': {'importacao': {'__all__': ['Nenhum registro recebido.']}}}, status=400)
 
    OBRIG = ['documento', 'matricula', 'referencia', 'saldo_devedor', 'prazo_faltante', 'parcela', 'taxa']
 
    criados = 0; atualizados = 0; erros = 0; log_erros = []
 
    for reg in registros:
        doc_raw   = re.sub(r'\D', '', str(reg.get('documento', '')))
        matricula = str(reg.get('matricula', '')).strip()
        ref_raw   = str(reg.get('referencia', '')).strip()
 
        falta = [f for f in OBRIG if not str(reg.get(f, '')).strip()]
        if falta:
            erros += 1
            log_erros.append({'documento': doc_raw or '?', 'erro': f'Campos obrigatórios vazios: {", ".join(falta)}'})
            if not pular_erros: break
            continue
 
        referencia = _parse_data(ref_raw)
        if not referencia:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': f'Data de referência inválida: "{ref_raw}"'})
            if not pular_erros: break
            continue
 
        saldo   = _decimal(reg.get('saldo_devedor'))
        prazo   = _inteiro(reg.get('prazo_faltante'))
        parcela = _decimal(reg.get('parcela'))
        taxa    = _decimal(reg.get('taxa'))
 
        if any(v is None for v in [saldo, prazo, parcela, taxa]):
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': 'Valores numéricos inválidos (saldo, prazo, parcela ou taxa).'})
            if not pular_erros: break
            continue
 
        cliente = _achar_cliente(empresa, doc_raw)
        if not cliente:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': 'Cliente não encontrado.'})
            if not pular_erros: break
            continue
 
        vinculo = _achar_vinculo(empresa, cliente, matricula)
        if not vinculo:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': f'Vínculo com matrícula "{matricula}" não encontrado. Importe os vínculos primeiro.'})
            if not pular_erros: break
            continue
 
        banco    = str(reg.get('banco',    '') or '').strip() or None
        rubrica  = str(reg.get('rubrica',  '') or '').strip() or None
        tipo     = str(reg.get('tipo',     '') or '').strip() or None
        contrato = str(reg.get('contrato', '') or '').strip() or None
 
        defaults = {
            'banco':          banco,
            'rubrica':        rubrica,
            'Tipo':           tipo,
            'saldo_devedor':  saldo,
            'prazo_faltante': prazo,
            'parcela':        parcela,
            'taxa':           taxa,
        }
 
        try:
            with transaction.atomic():
                if contrato:
                    # Upsert por contrato + referencia
                    obj, criado = Divida.objects.update_or_create(
                        empresa=empresa,
                        vinculo=vinculo,
                        contrato=contrato,
                        referencia=referencia,
                        defaults=defaults,
                    )
                else:
                    # Sem contrato → cria sempre (dívidas sem identificador único)
                    obj = Divida.objects.create(
                        empresa=empresa,
                        vinculo=vinculo,
                        contrato=None,
                        referencia=referencia,
                        **defaults,
                    )
                    criado = True
 
            if criado: criados += 1
            else:      atualizados += 1
 
        except (ValidationError, IntegrityError) as exc:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': _msg(exc)})
            if not pular_erros: break
        except Exception as exc:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': str(exc)})
            if not pular_erros: break
 
    return JsonResponse({'criados': criados, 'atualizados': atualizados,
                         'erros': erros, 'log_erros': log_erros})



@login_required
@require_POST
def importar_veiculos_csv(request):
    """
    Payload: { "registros": [...], "pular_erros": true }
 
    Colunas CSV:
        obrigatório: documento
        opcionais:   placa, chassi, renavan, marca, modelo,
                     ano_fab, ano_mod, cat
 
    Lógica:
        - Se placa informada → update_or_create por (empresa, cliente, placa)
        - Sem placa          → create sempre
    """
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'messages': {'importacao': {'__all__': ['JSON inválido']}}}, status=400
        )
 
    registros   = data.get('registros', [])
    pular_erros = data.get('pular_erros', True)
    empresa     = request.empresa
 
    if not registros:
        return JsonResponse(
            {'messages': {'importacao': {'__all__': ['Nenhum registro recebido.']}}}, status=400
        )
 
    criados = 0; atualizados = 0; erros = 0; log_erros = []
 
    for reg in registros:
        doc_raw = re.sub(r'\D', '', str(reg.get('documento', '')))
 
        if not doc_raw:
            erros += 1
            log_erros.append({'documento': '?', 'erro': 'Campo documento ausente.'})
            if not pular_erros: break
            continue
 
        cliente = _achar_cliente(empresa, doc_raw)
        if not cliente:
            erros += 1
            log_erros.append({'documento': doc_raw,
                               'erro': 'Cliente não encontrado. Importe o cadastro primeiro.'})
            if not pular_erros: break
            continue
 
        placa   = str(reg.get('placa',   '') or '').strip().upper() or None
        chassi  = str(reg.get('chassi',  '') or '').strip().upper() or None
        renavan = str(reg.get('renavan', '') or '').strip()         or None
        marca   = str(reg.get('marca',   '') or '').strip().upper() or None
        modelo  = str(reg.get('modelo',  '') or '').strip()         or None
        ano_fab = str(reg.get('ano_fab', '') or '').strip()         or None
        ano_mod = str(reg.get('ano_mod', '') or '').strip()         or None
        cat_raw = str(reg.get('cat',     '') or '').strip().upper() or None
 
        # Normaliza categoria
        cat = cat_raw if cat_raw in CHOICE_CAT_VALIDOS else None
        if cat_raw and not cat:
            # tenta match parcial: "carro" → CARROS, "moto" → MOTO, "caminhao" → CAMINHOES
            for key in CHOICE_CAT_VALIDOS:
                if key.startswith(cat_raw[:4]):
                    cat = key
                    break
 
        defaults = {
            'chassi':  chassi,
            'renavan': renavan,
            'marca':   marca,
            'modelo':  modelo,
            'ano_fab': ano_fab,
            'ano_mod': ano_mod,
            'cat':     cat,
        }
 
        try:
            with transaction.atomic():
                if placa:
                    obj, criado = Veiculo.objects.update_or_create(
                        empresa=empresa,
                        cliente=cliente,
                        placa=placa,
                        defaults=defaults,
                    )
                else:
                    Veiculo.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        placa=None,
                        **defaults,
                    )
                    criado = True
 
            if criado: criados += 1
            else:      atualizados += 1
 
        except (ValidationError, IntegrityError) as e:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': _msg_erro(e)})
            if not pular_erros: break
        except Exception as e:
            erros += 1
            log_erros.append({'documento': doc_raw, 'erro': str(e)})
            if not pular_erros: break
 
    return JsonResponse({'criados': criados, 'atualizados': atualizados,
                         'erros': erros, 'log_erros': log_erros})