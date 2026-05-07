// importar_clientes.js — Importação em lote de clientes via CSV

// ── Estado ────────────────────────────────────────────────
const ESTADO = {
    linhasParseadas: [],
    headersCSV:      [],
    errosValidacao:  [],
};

// Colunas aceitas
// Telefones: telefone1, telefone1_tipo, telefone2, telefone2_tipo, ...  (até 3)
// Emails:    email1,    email1_tipo,    email2,    email2_tipo, ...     (até 3)
const COLUNAS_OBRIGATORIAS = ['nome', 'documento', 'tipo_pessoa'];
const COLUNAS_CLIENTE      = [
    'nome', 'documento', 'tipo_pessoa',
    'data_nascimento', 'nome_mae', 'estado_civil',
];
const COLUNAS_TELEFONE = [
    'telefone1', 'telefone1_tipo',
    'telefone2', 'telefone2_tipo',
    'telefone3', 'telefone3_tipo',
];
const COLUNAS_EMAIL = [
    'email1', 'email1_tipo',
    'email2', 'email2_tipo',
    'email3', 'email3_tipo',
];
const TODAS_COLUNAS = [...COLUNAS_CLIENTE, ...COLUNAS_TELEFONE, ...COLUNAS_EMAIL];

const ESTADOS_CIVIS_VALIDOS = ['SOLTEIRO','CASADO','DIVORCIADO','VIUVO','UNIAO_ESTAVEL'];
const TIPOS_PESSOA_VALIDOS  = ['PF','PJ'];
const TIPOS_TELEFONE_VALIDOS = ['FIXO','CELULAR','CORPORATIVO'];
const TIPOS_EMAIL_VALIDOS    = ['PESSOAL','CORPORATIVO'];

// Modelo para download
const MODELO_CSV = [
    'nome,documento,tipo_pessoa,data_nascimento,nome_mae,estado_civil,' +
    'telefone1,telefone1_tipo,telefone2,telefone2_tipo,telefone3,telefone3_tipo,'+
    'email1,email1_tipo,email2,email2_tipo',

    'João Silva,12345678901,PF,15/06/1990,Maria Silva,SOLTEIRO,'+
    '11987654321,CELULAR,1133334444,FIXO,,,joao@email.com,PESSOAL,,',

    'Empresa LTDA,12774041000165,PJ,,,,1133334444,FIXO,11988887777,CORPORATIVO,,,'+
    'contato@empresa.com,CORPORATIVO,financeiro@empresa.com,CORPORATIVO',
].join('\n');

// ── Upload ─────────────────────────────────────────────────
const icDrop = document.getElementById('icDrop');

function handleDrop(event) {
    event.preventDefault();
    icDrop.classList.remove('ic-drop--over');
    const file = event.dataTransfer.files[0];
    if (file) processarArquivo(file);
}

function handleFileInput(input) {
    if (input.files[0]) processarArquivo(input.files[0]);
}

function processarArquivo(file) {
    if (!file.name.match(/\.(csv|txt)$/i)) {
        mostrarErroRapido('Formato inválido. Use arquivos .csv separados por ,'); return;
    }
    if (file.size > 10 * 1024 * 1024) {
        mostrarErroRapido('Arquivo muito grande. Limite: 5 MB'); return;
    }

    document.getElementById('icDropIlustracao').style.display = 'none';
    document.getElementById('icDropTitulo').style.display     = 'none';
    document.getElementById('icArquivoSelecionado').style.display = 'flex';
    document.getElementById('icArquivoNome').textContent      = file.name;
    document.getElementById('icArquivoTamanho').textContent   = formatarTamanho(file.size);

    const reader = new FileReader();
    reader.onload = (e) => parsearCSV(e.target.result);
    reader.readAsText(file, 'UTF-8');
}

function removerArquivo() {
    ESTADO.linhasParseadas = [];
    ESTADO.headersCSV      = [];
    ESTADO.errosValidacao  = [];

    document.getElementById('icArquivoSelecionado').style.display = 'none';
    document.getElementById('icDropIlustracao').style.display     = '';
    document.getElementById('icDropTitulo').style.display         = '';
    document.getElementById('icFile').value                       = '';

    ocultarTudo();
    document.getElementById('icPlaceholder').style.display  = 'flex';
    document.getElementById('icCardOpcoes').style.display   = 'none';
    document.getElementById('icBtnImportar').style.display  = 'none';
}

// ── Parse CSV ──────────────────────────────────────────────
function parsearCSV(texto) {
    const linhas = texto.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);

    if (linhas.length < 2) {
        mostrarErroRapido('O arquivo está vazio ou contém apenas o cabeçalho.'); return;
    }

    const sep     = linhas[0].includes(';') ? ';' : ',';
    const headers = linhas[0].split(sep).map(h => h.trim().toLowerCase().replace(/^"|"$/g, ''));

    ESTADO.headersCSV = headers;

    const faltando = COLUNAS_OBRIGATORIAS.filter(c => !headers.includes(c));
    if (faltando.length) {
        mostrarErroRapido(`Coluna(s) obrigatória(s) não encontrada(s): ${faltando.join(', ')}`);
        return;
    }

    const registros = [];
    for (let i = 1; i < linhas.length; i++) {
        const cols = parseLinha(linhas[i], sep);
        const obj  = {};
        headers.forEach((h, idx) => { obj[h] = (cols[idx] || '').trim(); });
        obj._linha = i + 1;
        registros.push(obj);
    }

    ESTADO.linhasParseadas = registros;
    renderizarPreview(registros, headers);
    validarRegistros(registros);
}

function parseLinha(linha, sep) {
    const res = [];
    let atual = '', aspas = false;
    for (const ch of linha) {
        if (ch === '"')           { aspas = !aspas; }
        else if (ch === sep && !aspas) { res.push(atual); atual = ''; }
        else                      { atual += ch; }
    }
    res.push(atual);
    return res;
}

// ── Preview ────────────────────────────────────────────────
function renderizarPreview(registros, headers) {
    const MAX   = 10;
    const cols  = headers.filter(h => TODAS_COLUNAS.includes(h));
    const extra = headers.filter(h => !TODAS_COLUNAS.includes(h));

    const thHtml = cols.map(h => {
        const cls = COLUNAS_OBRIGATORIAS.includes(h) ? ' ic-th--required' : '';
        return `<th class="${cls}">${h}</th>`;
    }).join('');

    const trHtml = registros.slice(0, MAX).map(r =>
        `<tr>${cols.map(h => {
            const v = r[h] || '';
            return `<td class="${v ? '' : 'ic-td--empty'}">${escapeHtml(v || '—')}</td>`;
        }).join('')}</tr>`
    ).join('');

    document.getElementById('icPreviewTable').innerHTML =
        `<thead><tr>${thHtml}</tr></thead><tbody>${trHtml}</tbody>`;
    document.getElementById('icPreviewBadge').textContent =
        `${registros.length} registro${registros.length !== 1 ? 's' : ''}`;

    const notas = [];
    if (registros.length > MAX) notas.push(`Exibindo ${MAX} de ${registros.length} registros.`);
    if (extra.length)           notas.push(`Colunas ignoradas: ${extra.join(', ')}.`);
    document.getElementById('icPreviewNota').textContent = notas.join(' ');

    document.getElementById('icPlaceholder').style.display = 'none';
    document.getElementById('icCardPreview').style.display = 'block';
}

// ── Validação local ────────────────────────────────────────
function validarRegistros(registros) {
    const erros = [];

    registros.forEach(r => {
        const linha = r._linha;

        // Obrigatórios básicos
        if (!r.nome?.trim()) {
            erros.push({ linha, msg: 'Campo "nome" vazio.', tipo: 'erro' }); return;
        }

        const doc = (r.documento || '').replace(/\D/g, '');
        if (!doc) {
            erros.push({ linha, msg: 'Campo "documento" vazio.', tipo: 'erro' }); return;
        }
        if (doc.length !== 11 && doc.length !== 14) {
            erros.push({ linha, msg: `Documento inválido: "${r.documento}" (deve ter 11 ou 14 dígitos).`, tipo: 'warn' }); return;
        }

        const tp = (r.tipo_pessoa || '').toUpperCase().trim();
        if (!TIPOS_PESSOA_VALIDOS.includes(tp)) {
            erros.push({ linha, msg: `tipo_pessoa inválido: "${r.tipo_pessoa}". Use PF ou PJ.`, tipo: 'erro' }); return;
        }
        if (tp === 'PF' && doc.length !== 11) {
            erros.push({ linha, msg: `CPF deve ter 11 dígitos (encontrado: ${doc.length}).`, tipo: 'erro' }); return;
        }
        if (tp === 'PJ' && doc.length !== 14) {
            erros.push({ linha, msg: `CNPJ deve ter 14 dígitos (encontrado: ${doc.length}).`, tipo: 'erro' }); return;
        }

        // Data de nascimento
        if (r.data_nascimento && !r.data_nascimento.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
            erros.push({ linha, msg: `data_nascimento inválida: "${r.data_nascimento}". Use DD/MM/AAAA.`, tipo: 'warn' });
        }

        // Estado civil
        if (r.estado_civil) {
            const ec = r.estado_civil.toUpperCase().trim();
            if (!ESTADOS_CIVIS_VALIDOS.includes(ec)) {
                erros.push({
                    linha,
                    msg: `estado_civil inválido: "${r.estado_civil}". Aceitos: ${ESTADOS_CIVIS_VALIDOS.join(', ')}.`,
                    tipo: 'warn',
                });
            }
        }

        // Telefones (1–3)
        for (let i = 1; i <= 3; i++) {
            const fone = (r[`telefone${i}`] || '').replace(/\D/g, '');
            const tipo = (r[`telefone${i}_tipo`] || '').toUpperCase().trim();
            if (!fone) continue;
            if (fone.length < 10 || fone.length > 11)
                erros.push({ linha, msg: `telefone${i} inválido: "${r[`telefone${i}`]}" (10 ou 11 dígitos).`, tipo: 'warn' });
            if (tipo && !TIPOS_TELEFONE_VALIDOS.includes(tipo))
                erros.push({ linha, msg: `telefone${i}_tipo inválido: "${tipo}". Use FIXO, CELULAR ou CORPORATIVO.`, tipo: 'warn' });
        }

        // E-mails (1–3)
        for (let i = 1; i <= 3; i++) {
            const mail = (r[`email${i}`] || '').trim();
            const tipo = (r[`email${i}_tipo`] || '').toUpperCase().trim();
            if (!mail) continue;
            if (!mail.includes('@') || !mail.split('@')[1]?.includes('.'))
                erros.push({ linha, msg: `email${i} inválido: "${mail}".`, tipo: 'warn' });
            if (tipo && !TIPOS_EMAIL_VALIDOS.includes(tipo))
                erros.push({ linha, msg: `email${i}_tipo inválido: "${tipo}". Use PESSOAL ou CORPORATIVO.`, tipo: 'warn' });
        }
    });

    const totalErros = erros.filter(e => e.tipo === 'erro').length;
    const totalWarn  = erros.filter(e => e.tipo === 'warn').length;
    const totalOk    = registros.length - totalErros;
    ESTADO.errosValidacao = erros;

    document.getElementById('icValidacaoResumo').innerHTML = `
        <div class="ic-validacao-resumo">
            <div class="ic-val-card ic-val-card--total">
                <span class="ic-val-num">${registros.length}</span>
                <span class="ic-val-label">Total</span>
            </div>
            <div class="ic-val-card ic-val-card--ok">
                <span class="ic-val-num">${totalOk}</span>
                <span class="ic-val-label">Válidos</span>
            </div>
            <div class="ic-val-card ic-val-card--warn">
                <span class="ic-val-num">${totalWarn}</span>
                <span class="ic-val-label">Avisos</span>
            </div>
            <div class="ic-val-card ic-val-card--erro">
                <span class="ic-val-num">${totalErros}</span>
                <span class="ic-val-label">Erros</span>
            </div>
        </div>`;

    document.getElementById('icValidacaoIcone').textContent =
        totalErros > 0 ? '⚠️' : totalWarn > 0 ? '🟡' : '✅';

    const listaEl = document.getElementById('icErrosLista');
    listaEl.innerHTML = erros.length
        ? erros.slice(0, 50).map(e => `
            <div class="ic-erro-item ic-erro-item--${e.tipo}">
                <span class="ic-erro-linha">Linha ${e.linha}</span>
                <span class="ic-erro-msg">${escapeHtml(e.msg)}</span>
            </div>`).join('') +
          (erros.length > 50 ? `<p style="font-size:11px;color:#aaa;padding:6px 0">... e mais ${erros.length - 50} problema(s).</p>` : '')
        : `<p style="font-size:13px;color:#1e8449;font-weight:600;padding:6px 0">✓ Todos os registros passaram na validação.</p>`;

    document.getElementById('icCardValidacao').style.display = 'block';
    document.getElementById('icCardOpcoes').style.display    = 'block';
    document.getElementById('icBtnImportar').style.display   = 'inline-flex';
    document.getElementById('icBtnImportar').disabled        = (totalOk === 0);
}

// ── Importação em lotes ────────────────────────────────────
async function iniciarImportacao() {
    const registros = ESTADO.linhasParseadas;
    if (!registros.length) return;

    const pularErros = document.getElementById('optPularErros').checked;
    const upsert     = document.getElementById('optUpsert').checked;

    ocultarTudo();
    document.getElementById('icCardProgresso').style.display = 'block';
    document.getElementById('icBtnImportar').disabled        = true;

    const LOTE  = 50;
    const lotes = [];
    for (let i = 0; i < registros.length; i += LOTE)
        lotes.push(registros.slice(i, i + LOTE));

    let criados = 0, atualizados = 0, erros = 0;
    const logErros = [];

    for (let i = 0; i < lotes.length; i++) {
        atualizarProgresso(
            Math.round((i / lotes.length) * 100),
            `Processando lote ${i + 1} de ${lotes.length}...`
        );

        try {
            const resp = await fetch('/clientes/importar_csv/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ clientes: lotes[i], pular_erros: pularErros, upsert }),
            });

            const data = await resp.json();
            if (!resp.ok && !pularErros)
                throw new Error(data?.messages?.importacao?.__all__?.[0] || 'Erro no servidor.');

            criados     += data.criados     || 0;
            atualizados += data.atualizados || 0;
            erros       += data.erros       || 0;
            if (data.log_erros?.length) logErros.push(...data.log_erros);

        } catch (err) {
            atualizarProgresso(Math.round((i / lotes.length) * 100), 'Erro durante a importação.');
            renderizarResultado(criados, atualizados, erros, logErros);
            document.getElementById('icBtnImportar').disabled = false;
            return;
        }
    }

    atualizarProgresso(100, 'Importação concluída!');
    await sleep(500);
    document.getElementById('icCardProgresso').style.display = 'none';
    renderizarResultado(criados, atualizados, erros, logErros);
    document.getElementById('icBtnImportar').disabled = false;
}

function atualizarProgresso(pct, detalhe) {
    document.getElementById('icProgressoBar').style.width     = `${pct}%`;
    document.getElementById('icProgressoTexto').textContent   = `${pct}%`;
    document.getElementById('icProgressoDetalhe').textContent = detalhe;
}

function renderizarResultado(criados, atualizados, erros, logErros) {
    document.getElementById('icResultadoGrid').innerHTML = `
        <div class="ic-res-card ic-res-card--total">
            <span class="ic-res-num">${criados + atualizados + erros}</span>
            <span class="ic-res-label">Processados</span>
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
        </div>`;

    const logEl = document.getElementById('icLogErros');
    logEl.innerHTML = logErros.length ? `
        <p class="ic-log-titulo">
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.4"/>
                <path d="M7 4v4M7 9.5v.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            </svg>
            Registros com erro (${logErros.length})
        </p>
        <div class="ic-log-lista">
            ${logErros.slice(0, 100).map(e => `
                <div class="ic-erro-item ic-erro-item--erro">
                    <span class="ic-erro-linha">${escapeHtml(String(e.documento || '—'))}</span>
                    <span class="ic-erro-msg">${escapeHtml(e.erro || '')}</span>
                </div>`).join('')}
            ${logErros.length > 100 ? `<p style="font-size:11px;color:#aaa;padding:4px 0">... e mais ${logErros.length - 100} erro(s).</p>` : ''}
        </div>` : '';

    document.getElementById('icCardResultado').style.display = 'block';
}

// ── Reiniciar ──────────────────────────────────────────────
function reiniciar() {
    ESTADO.linhasParseadas = [];
    ESTADO.headersCSV      = [];
    ESTADO.errosValidacao  = [];
    document.getElementById('icFile').value                       = '';
    document.getElementById('icArquivoSelecionado').style.display = 'none';
    document.getElementById('icDropIlustracao').style.display     = '';
    document.getElementById('icDropTitulo').style.display         = '';
    ocultarTudo();
    document.getElementById('icPlaceholder').style.display  = 'flex';
    document.getElementById('icCardOpcoes').style.display   = 'none';
    document.getElementById('icBtnImportar').style.display  = 'none';
    document.getElementById('icBtnImportar').disabled       = false;
    atualizarProgresso(0, 'Iniciando importação...');
}

// ── Download do modelo ─────────────────────────────────────
function baixarModelo(event) {
    event.preventDefault();
    const blob = new Blob([MODELO_CSV], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: 'modelo_importacao_clientes.csv' });
    a.click();
    URL.revokeObjectURL(url);
}

// ── Helpers ────────────────────────────────────────────────
function ocultarTudo() {
    ['icCardPreview','icCardValidacao','icCardProgresso','icCardResultado','icPlaceholder']
        .forEach(id => { document.getElementById(id).style.display = 'none'; });
}

function mostrarErroRapido(msg) {
    document.getElementById('icPlaceholder').style.display    = 'none';
    document.getElementById('icCardValidacao').style.display  = 'block';
    document.getElementById('icValidacaoIcone').textContent   = '❌';
    document.getElementById('icValidacaoResumo').innerHTML    = '';
    document.getElementById('icErrosLista').innerHTML         = `
        <div class="ic-erro-item ic-erro-item--erro">
            <span class="ic-erro-msg" style="font-weight:600">${escapeHtml(msg)}</span>
        </div>`;
    document.getElementById('icCardOpcoes').style.display  = 'none';
    document.getElementById('icBtnImportar').style.display = 'none';
}

function formatarTamanho(bytes) {
    if (bytes < 1024)      return `${bytes} B`;
    if (bytes < 1048576)   return `${(bytes/1024).toFixed(1)} KB`;
    return `${(bytes/1048576).toFixed(1)} MB`;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }