// importar_financeiro.js
// Gerencia upload/validação/importação das 3 sub-tabs: vinculo, financeiro, dividas
// Depende de getCookie() definida em importar_clientes.js

// ── Configuração por tipo ──────────────────────────────────
const FIN_CONFIG = {
    vinculo: {
        url:          '/clientes/importar_vinculo_csv/',
        obrigatorios: ['documento', 'matricula'],
        modelo_header: 'documento,matricula,convenio,orgao,instituidor,sit_func',
        modelo_linhas: [
            '12345678901,1234567,SIAPE,MINISTERIO DA SAUDE,00000001,ATIVO',
            '98765432100,7654321,INSS,,,'
        ],
        modelo_nome: 'modelo_vinculo.csv',
    },
    financeiro: {
        url:          '/clientes/importar_financeiro_csv/',
        obrigatorios: ['documento', 'matricula', 'referencia', 'salario', 'margem_consig', 'margem_ct', 'margem_ct_bn'],
        modelo_header: 'documento,matricula,referencia,salario,margem_consig,margem_ct,margem_ct_bn',
        modelo_linhas: [
            '12345678901,1234567,01/05/2025,5000.00,1200.00,300.00,150.00',
            '12345678901,9876543,01/05/2025,3200.00,800.00,200.00,100.00',
            '98765432100,7654321,01/05/2025,3800.00,900.00,220.00,110.00'
        ],
        modelo_nome: 'modelo_financeiro.csv',
    },
    dividas: {
        url:          '/clientes/importar_dividas_csv/',
        obrigatorios: ['documento', 'matricula', 'referencia', 'saldo_devedor', 'prazo_faltante', 'parcela', 'taxa'],
        modelo_header: 'documento,matricula,referencia,saldo_devedor,prazo_faltante,parcela,taxa,banco,rubrica,tipo,contrato',
        modelo_linhas: [
            '12345678901,1234567,01/05/2025,12000.00,48,250.00,1.80,104,026,RCC,123456',
            '12345678901,1234567,01/05/2025,5000.00,24,208.33,2.10,033,001,RMC,654321',
            '12345678901,1234567,01/05/2025,8000.00,36,222.22,1.95,341,,,789012',
            '98765432100,7654321,01/05/2025,3000.00,12,250.00,2.50,104,026,RCC,'
        ],
        modelo_nome: 'modelo_dividas.csv',
    },
};

// Prefixo → tipo
const FIN_PREFIXO = { vinculo: 'vinc', financeiro: 'fin', dividas: 'div' };

// Estado por tipo
const FIN_ESTADO = {
    vinculo:    { linhas: [], headers: [] },
    financeiro: { linhas: [], headers: [] },
    dividas:    { linhas: [], headers: [] },
};

// ── Navegação tab principal / sub-tabs ────────────────────
function icSetTab(tabName) {
    document.querySelectorAll('.ic-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.ic-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`.ic-tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`panel-${tabName}`).classList.add('active');
}

function icSetSubtab(subtabName) {
    document.querySelectorAll('.ic-subtab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.ic-subpanel').forEach(p => p.classList.remove('active'));
    document.querySelector(`.ic-subtab[data-subtab="${subtabName}"]`).classList.add('active');
    document.getElementById(`subpanel-${subtabName}`).classList.add('active');
}

// ── Upload ────────────────────────────────────────────────
function finHandleDrop(event, tipo) {
    event.preventDefault();
    const pref = FIN_PREFIXO[tipo];
    document.getElementById(`${pref}-drop`).classList.remove('ic-drop--over');
    const file = event.dataTransfer.files[0];
    if (file) _finProcessar(file, tipo);
}

function finHandleFile(input, tipo) {
    if (input.files[0]) _finProcessar(input.files[0], tipo);
}

function finRemover(tipo) {
    const pref = FIN_PREFIXO[tipo];
    document.getElementById(`${pref}-file`).value = '';
    document.getElementById(`${pref}-arquivo`).style.display = 'none';
    document.getElementById(`${pref}-drop`).style.display    = 'block';
    document.getElementById(`${pref}-btn-importar`).style.display = 'none';
    document.getElementById(`${pref}-placeholder`).style.display  = 'flex';
    document.getElementById(`${pref}-cards`).innerHTML = '';
    FIN_ESTADO[tipo] = { linhas: [], headers: [] };
}

function _finProcessar(file, tipo) {
    if (!file.name.match(/\.(csv|txt)$/i)) { alert('Use arquivos .csv'); return; }
    if (file.size > 10 * 1024 * 1024)     { alert('Arquivo muito grande. Máx. 5 MB.'); return; }

    const pref = FIN_PREFIXO[tipo];
    document.getElementById(`${pref}-arquivo-nome`).textContent = file.name;
    document.getElementById(`${pref}-arquivo-tam`).textContent  = _finTamanho(file.size);
    document.getElementById(`${pref}-arquivo`).style.display    = 'flex';
    document.getElementById(`${pref}-drop`).style.display       = 'none';
    document.getElementById(`${pref}-placeholder`).style.display = 'none';

    const reader = new FileReader();
    reader.onload = e => _finParseCSV(e.target.result, tipo);
    reader.readAsText(file, 'UTF-8');
}

// ── Parse ─────────────────────────────────────────────────
function _finParseCSV(texto, tipo) {
    const linhas = texto.trim().split('\n').map(l => l.trim()).filter(Boolean);
    if (linhas.length < 2) { alert('CSV vazio ou sem dados.'); return; }

    const headers = linhas[0].split(',').map(h => h.trim().toLowerCase().replace(/[\r"]/g, ''));
    const cfg     = FIN_CONFIG[tipo];
    const falta   = cfg.obrigatorios.filter(c => !headers.includes(c));
    if (falta.length) { alert(`Colunas obrigatórias ausentes: ${falta.join(', ')}`); return; }

    const registros = linhas.slice(1).map(l => {
        const vals = _finSplit(l);
        const obj  = {};
        headers.forEach((h, i) => { obj[h] = (vals[i] || '').trim().replace(/^"|"$/g, ''); });
        return obj;
    });

    FIN_ESTADO[tipo] = { linhas: registros, headers };
    _finRenderCards(tipo, registros, headers);
}

function _finSplit(linha) {
    const res = []; let cur = ''; let q = false;
    for (const ch of linha) {
        if (ch === '"') { q = !q; }
        else if (ch === ',' && !q) { res.push(cur); cur = ''; }
        else { cur += ch; }
    }
    res.push(cur);
    return res;
}

// ── Renderiza cards (preview + validação + opções) ────────
function _finRenderCards(tipo, registros, headers) {
    const pref      = FIN_PREFIXO[tipo];
    const cfg       = FIN_CONFIG[tipo];
    const container = document.getElementById(`${pref}-cards`);

    // ── validação ──
    const erros   = [];
    let totalOk   = 0, totalErro = 0;

    registros.forEach((reg, i) => {
        const linha  = i + 2;
        const falta  = cfg.obrigatorios.filter(f => !reg[f] || !reg[f].trim());
        if (falta.length) {
            erros.push({ linha, msg: `Campos obrigatórios vazios: ${falta.join(', ')}.` });
            totalErro++;
        } else {
            totalOk++;
        }
    });

    const icone = totalErro > 0 ? '❌' : '✅';

    // ── HTML dos cards ──
    const visiveisCols = headers.slice(0, 8); // máx 8 colunas no preview

    container.innerHTML = `

        <!-- Preview -->
        <div class="ic-card" style="margin-bottom:16px">
            <div class="ic-card__head">
                <span class="ic-card__icon">👁️</span>
                <h3 class="ic-card__title">Pré-visualização</h3>
                <span class="ic-preview-badge">${registros.length} linha(s)</span>
            </div>
            <div class="ic-card__body ic-card__body--no-pad">
                <div class="ic-preview-wrap">
                    <table class="ic-preview-table">
                        <thead><tr>${visiveisCols.map(h =>
                            `<th class="${cfg.obrigatorios.includes(h) ? 'ic-th--required' : ''}">${_finEsc(h)}</th>`
                        ).join('')}${headers.length > 8 ? `<th style="color:#aaa">+${headers.length - 8}</th>` : ''}</tr></thead>
                        <tbody>${registros.slice(0, 5).map(r =>
                            `<tr>${visiveisCols.map(h =>
                                `<td class="${!r[h] ? 'ic-td--empty' : ''}">${_finEsc(r[h] || '—')}</td>`
                            ).join('')}${headers.length > 8 ? '<td style="color:#ddd">…</td>' : ''}</tr>`
                        ).join('')}</tbody>
                    </table>
                </div>
                <p class="ic-preview-nota">Exibindo até 5 linhas. Valide antes de importar.</p>
            </div>
        </div>

        <!-- Validação -->
        <div class="ic-card" style="margin-bottom:16px">
            <div class="ic-card__head">
                <span class="ic-card__icon">${icone}</span>
                <h3 class="ic-card__title">Resultado da Validação</h3>
            </div>
            <div class="ic-card__body">
                <div class="ic-validacao-resumo">
                    <div class="ic-val-card ic-val-card--total">
                        <span class="ic-val-num">${registros.length}</span>
                        <span class="ic-val-label">Total</span>
                    </div>
                    <div class="ic-val-card ic-val-card--ok">
                        <span class="ic-val-num">${totalOk}</span>
                        <span class="ic-val-label">OK</span>
                    </div>
                    <div class="ic-val-card ic-val-card--erro">
                        <span class="ic-val-num">${totalErro}</span>
                        <span class="ic-val-label">Erros</span>
                    </div>
                </div>
                <div class="ic-erros-lista">
                    ${erros.length
                        ? erros.slice(0, 30).map(e =>
                            `<div class="ic-erro-item ic-erro-item--erro">
                                <span class="ic-erro-linha">Linha ${e.linha}</span>
                                <span class="ic-erro-msg">${_finEsc(e.msg)}</span>
                            </div>`).join('') +
                          (erros.length > 30 ? `<p style="font-size:11px;color:#aaa">... e mais ${erros.length - 30} erro(s).</p>` : '')
                        : `<p style="font-size:13px;color:#1e8449;font-weight:600;padding:6px 0">✓ Todos os registros passaram na validação.</p>`
                    }
                </div>
            </div>
        </div>

        <!-- Opções -->
        <div class="ic-card" style="margin-bottom:16px">
            <div class="ic-card__head">
                <span class="ic-card__icon">⚙️</span>
                <h3 class="ic-card__title">Opções de Importação</h3>
            </div>
            <div class="ic-card__body">
                <div class="ic-opcoes-grid">
                    <label class="ic-opcao-item">
                        <div class="ic-opcao-toggle">
                            <input type="checkbox" id="${pref}-opt-pular" checked>
                            <span class="ic-opcao-knob"></span>
                        </div>
                        <div class="ic-opcao-texto">
                            <span class="ic-opcao-label">Continuar em caso de erro</span>
                            <span class="ic-opcao-desc">Linhas inválidas são registradas no log e puladas</span>
                        </div>
                    </label>
                </div>
            </div>
        </div>
    `;

    // Exibe botão importar se há linhas válidas
    document.getElementById(`${pref}-btn-importar`).style.display = totalOk > 0 ? 'inline-flex' : 'none';
    document.getElementById(`${pref}-btn-importar`).disabled      = (totalOk === 0);
}

// ── Importação em lotes ───────────────────────────────────
async function finImportar(tipo) {
    const pref    = FIN_PREFIXO[tipo];
    const cfg     = FIN_CONFIG[tipo];
    const estado  = FIN_ESTADO[tipo];
    if (!estado.linhas.length) return;

    const pularErros = document.getElementById(`${pref}-opt-pular`)?.checked ?? true;
    const container  = document.getElementById(`${pref}-cards`);
    const btn        = document.getElementById(`${pref}-btn-importar`);

    // Injeta card de progresso
    container.insertAdjacentHTML('beforeend', `
        <div class="ic-card" id="${pref}-card-prog" style="margin-bottom:16px">
            <div class="ic-card__head">
                <span class="ic-card__icon">⏳</span>
                <h3 class="ic-card__title">Importando...</h3>
            </div>
            <div class="ic-card__body">
                <div class="ic-progresso">
                    <div class="ic-progresso__bar-wrap">
                        <div class="ic-progresso__bar" id="${pref}-prog-bar"></div>
                    </div>
                    <span class="ic-progresso__texto" id="${pref}-prog-txt">0%</span>
                </div>
                <p class="ic-progresso__detalhe" id="${pref}-prog-det">Iniciando...</p>
            </div>
        </div>
    `);
    btn.disabled = true;

    const LOTE  = 50;
    const lotes = [];
    for (let i = 0; i < estado.linhas.length; i += LOTE)
        lotes.push(estado.linhas.slice(i, i + LOTE));

    let criados = 0, atualizados = 0, erros = 0;
    const logErros = [];

    for (let i = 0; i < lotes.length; i++) {
        const pct = Math.round(((i + 1) / lotes.length) * 100);
        document.getElementById(`${pref}-prog-bar`).style.width     = pct + '%';
        document.getElementById(`${pref}-prog-txt`).textContent     = pct + '%';
        document.getElementById(`${pref}-prog-det`).textContent     = `Lote ${i + 1} de ${lotes.length}...`;

        try {
            const resp = await fetch(cfg.url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ registros: lotes[i], pular_erros: pularErros }),
            });
            const data = await resp.json();
            if (!resp.ok && !pularErros)
                throw new Error(data?.messages?.importacao?.__all__?.[0] || 'Erro no servidor.');
            criados     += data.criados     || 0;
            atualizados += data.atualizados || 0;
            erros       += data.erros       || 0;
            if (data.log_erros?.length) logErros.push(...data.log_erros);
        } catch (err) {
            logErros.push({ documento: '?', erro: err.message });
            erros++;
            if (!pularErros) break;
        }
    }

    // Substitui card progresso por resultado
    const cardProg = document.getElementById(`${pref}-card-prog`);
    if (cardProg) cardProg.remove();

    container.insertAdjacentHTML('beforeend', `
        <div class="ic-card" style="margin-bottom:16px">
            <div class="ic-card__head">
                <span class="ic-card__icon">🏁</span>
                <h3 class="ic-card__title">Resultado da Importação</h3>
            </div>
            <div class="ic-card__body">
                <div class="ic-resultado-grid">
                    <div class="ic-res-card ic-res-card--total">
                        <span class="ic-res-num">${estado.linhas.length}</span>
                        <span class="ic-res-label">Total</span>
                    </div>
                    <div class="ic-res-card ic-res-card--criado">
                        <span class="ic-res-num">${criados}</span>
                        <span class="ic-res-label">Criados</span>
                    </div>
                    <div class="ic-res-card ic-res-card--duplicado">
                        <span class="ic-res-num">${atualizados}</span>
                        <span class="ic-res-label">Atualizados</span>
                    </div>
                    <div class="ic-res-card ic-res-card--erro">
                        <span class="ic-res-num">${erros}</span>
                        <span class="ic-res-label">Erros</span>
                    </div>
                </div>
                ${logErros.length ? `
                    <p class="ic-log-titulo">⚠️ Log de erros (${logErros.length})</p>
                    <div class="ic-log-lista">
                        ${logErros.slice(0, 30).map(e =>
                            `<div class="ic-erro-item ic-erro-item--erro">
                                <span class="ic-erro-linha">${_finEsc(e.documento || '?')}</span>
                                <span class="ic-erro-msg">${_finEsc(e.erro)}</span>
                            </div>`).join('')}
                        ${logErros.length > 30 ? `<p style="font-size:11px;color:#aaa">... e mais ${logErros.length - 30}.</p>` : ''}
                    </div>` : ''}
                <div class="ic-resultado-acoes">
                    <button class="ic-btn ic-btn--ghost" onclick="finRemover('${tipo}')">Importar outro arquivo</button>
                </div>
            </div>
        </div>
    `);
}

// ── Download de modelo ────────────────────────────────────
function finBaixarModelo(e, tipo) {
    e.preventDefault();
    const cfg  = FIN_CONFIG[tipo];
    const csv  = [cfg.modelo_header, ...cfg.modelo_linhas].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = cfg.modelo_nome; a.click();
    URL.revokeObjectURL(url);
}

// ── Helpers ───────────────────────────────────────────────
function _finEsc(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _finTamanho(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}