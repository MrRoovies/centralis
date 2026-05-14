// campanhas_admin.js — Gestão de Campanhas

// ── Estado ──────────────────────────────────────────────────
let _modo       = null;   // 'campanha' | 'agentes' | 'mailing'
let _campanhaId = null;   // null = criação, number = edição
let _searchField = 'documento';
let _csvData     = [];    // linhas do CSV parseado

// ── Abrir drawer ─────────────────────────────────────────────
function abrirDrawer(modo, campanhaId) {
    _modo       = modo;
    _campanhaId = campanhaId;

    _resetDrawer();

    // Configura header e cores
    const configs = {
        campanha: {
            title:    campanhaId ? 'Editar Campanha' : 'Nova Campanha',
            subtitle: campanhaId ? 'Altere os campos desejados' : 'Preencha os dados abaixo',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <rect x="2" y="4" width="16" height="12" rx="2" stroke="white" stroke-width="1.6"/>
                       <path d="M2 8h16" stroke="white" stroke-width="1.6"/>
                       <path d="M6 12h8M6 14.5h4" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
                   </svg>`,
        },
        agentes: {
            title:    'Agentes da Campanha',
            subtitle: 'Vincule ou desvincule agentes',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <circle cx="8" cy="7" r="3.5" stroke="white" stroke-width="1.6"/>
                       <path d="M2 17c0-3.314 2.686-6 6-6" stroke="white" stroke-width="1.6" stroke-linecap="round"/>
                       <circle cx="15" cy="10" r="2.5" stroke="white" stroke-width="1.4"/>
                       <path d="M15 13v4M13 15h4" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
                   </svg>`,
        },
        mailing: {
            title:    'Mailing da Campanha',
            subtitle: 'Adicione ou importe clientes',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <path d="M3 3h14v14H3V3z" stroke="white" stroke-width="1.6" stroke-linejoin="round"/>
                       <path d="M3 7h14" stroke="white" stroke-width="1.4"/>
                       <path d="M7 7v10" stroke="white" stroke-width="1.4"/>
                       <path d="M7 11h7M7 14h4" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
                   </svg>`,
        }
    };

    const cfg = configs[modo];
    document.getElementById('caDrawerTitle').textContent    = cfg.title;
    document.getElementById('caDrawerSubtitle').textContent = cfg.subtitle;
    document.getElementById('caDrawerIcon').innerHTML       = cfg.icon;
    document.getElementById('caDrawerHeader').className =
        `ca-drawer__header ca-drawer__header--${modo}`;

    // Footer: só exibe para campanha
    document.getElementById('caDrawerFooter').style.display =
        modo === 'campanha' ? 'flex' : 'none';

    document.getElementById('caOverlay').classList.add('active');
    document.getElementById('caDrawer').classList.add('active');

    // Carrega conteúdo
    if (modo === 'campanha') {
        _carregarFormCampanha(campanhaId);
    } else if (modo === 'agentes') {
        _carregarAgentes(campanhaId);
    } else if (modo === 'mailing') {
        _carregarMailing(campanhaId);
    }
}

// ── Fechar drawer ────────────────────────────────────────────
function fecharDrawer() {
    document.getElementById('caOverlay').classList.remove('active');
    document.getElementById('caDrawer').classList.remove('active');
    _modo = null;
    _campanhaId = null;
    _csvData = [];
}

// ════════════════════════════════════════════════════════════
// CAMPANHA — criar / editar
// ════════════════════════════════════════════════════════════

function _carregarFormCampanha(campanhaId) {
    if (!campanhaId) {
        // Criação: apenas exibe o form vazio
        document.getElementById('caSpinner').style.display  = 'none';
        document.getElementById('formCampanha').style.display = 'block';
        return;
    }

    fetch(`/campanhas/admin/${campanhaId}/`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('caSpinner').style.display    = 'none';
            document.getElementById('formCampanha').style.display = 'block';

            const c = data.campanha;
            console.log(c);
            document.getElementById('cp_nome').value   = c.nome    || '';
            _setVal('cp_carteira', c.carteira_id);
            _setVal('cp_modo',     c.modo_atendimento);
            _setVal('cp_metodo',   c.metodo_distribuicao);
            _setVal('cp_msg_whats',   c.texto_whatsapp);

            const chk = document.getElementById('cp_ativo');
            chk.checked = c.distribuicao_ativa !== false;
            _atualizarToggleText('cp_ativo_text', chk.checked);
        })
        .catch(() => _mostrarFeedback('Erro ao carregar dados da campanha.', 'error'));
}

function salvarDrawer() {
    if (_modo !== 'campanha') return;

    _limparErros();

    const btn   = document.getElementById('caBtnSalvar');
    const label = document.getElementById('caBtnLabel');
    btn.disabled      = true;
    label.textContent = 'Salvando...';

    const nome   = document.getElementById('cp_nome').value.trim();
    const chk    = document.getElementById('cp_ativo');

    const payload = {
        nome:                 nome,
        carteira_id:          document.getElementById('cp_carteira').value,
        modo_atendimento:     document.getElementById('cp_modo').value,
        metodo_distribuicao:  document.getElementById('cp_metodo').value,
        msg_whatsapp:  document.getElementById('cp_msg_whats').value,
        distribuicao_ativa:   chk.checked,
    };

    const url    = _campanhaId
    ? `/campanhas/admin/${_campanhaId}/`
    : '/campanhas/admin/nova/';

    const method = 'POST';

    fetch(url, {
        method,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        _mostrarFeedback(
            d.messages?.campanha?.success?.[0] || '✓ Campanha salva com sucesso!',
            'success'
        );
        setTimeout(() => { fecharDrawer(); location.reload(); }, 900);
    })
    .catch(err => {
        const msgs = err?.messages?.campanha || {};
        let temCampo = false;

        Object.entries(msgs).forEach(([campo, erros]) => {
            const txt = Array.isArray(erros) ? erros.join(' ') : erros;
            if (campo === '__all__') {
                _mostrarFeedback(txt, 'error');
                return;
            }
            const errEl = document.getElementById(`err-cp-${campo}`);
            const inpEl = document.querySelector(`#formCampanha [name="${campo}"]`);
            if (errEl) { errEl.textContent = txt; errEl.style.display = 'block'; }
            if (inpEl) inpEl.classList.add('ca-form__input--error');
            temCampo = true;
        });

        if (!temCampo && !Object.keys(msgs).length)
            _mostrarFeedback('Erro ao salvar. Tente novamente.', 'error');
    })
    .finally(() => {
        btn.disabled      = false;
        label.textContent = _campanhaId ? 'Salvar' : 'Criar';
    });
}

// ── Toggle ativo da tabela ───────────────────────────────────
function toggleCampanha(campanhaId, btn) {
    const row = document.getElementById(`ca-row-${campanhaId}`);

    fetch(`/campanhas/admin/${campanhaId}/toggle/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const ativo    = d.distribuicao_ativa;
        const statusEl = row.querySelector('.ca-status');

        row.classList.toggle('ca-row--inativa', !ativo);
        statusEl.className = `ca-status ca-status--${ativo ? 'ativa' : 'inativa'}`;
        statusEl.innerHTML = `${ativo ? 'Ativa' : 'Inativa'}`;

        btn.innerHTML = ativo
            ? `<svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                   <rect x="2" y="2" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.4"/>
                   <path d="M4 7h6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
               </svg>`
            : `<svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                   <rect x="2" y="2" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.4"/>
                   <path d="M4 7l2.5 2.5L10 4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
               </svg>`;
    })
    .catch(() => _mostrarFeedback('Erro ao alterar status.', 'error'));
}


// ════════════════════════════════════════════════════════════
// AGENTES — vincular / desvincular
// ════════════════════════════════════════════════════════════

function _carregarAgentes(campanhaId) {
    fetch(`/campanhas/admin/${campanhaId}/agentes/`)
        .then(r => r.json())
        .then(data => {
            document.getElementById('caSpinner').style.display   = 'none';
            document.getElementById('painelAgentes').style.display = 'block';

            _renderizarAgentesVinculados(data.vinculados);

            // Popular select de disponíveis
            const sel = document.getElementById('selectNovoAgente');
            sel.innerHTML = '<option value="">Selecione um agente...</option>';
            (data.disponiveis || []).forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.id;
                opt.textContent = a.nome;
                sel.appendChild(opt);
            });
        })
        .catch(() => _mostrarFeedback('Erro ao carregar agentes.', 'error'));
}

function _renderizarAgentesVinculados(lista) {
    const container = document.getElementById('listaAgentesVinculados');
    if (!lista || lista.length === 0) {
        container.innerHTML = `
            <div class="ca-agentes-vazio">
                Nenhum agente vinculado a esta campanha.
            </div>`;
        return;
    }

    container.innerHTML = lista.map(a => {
        const iniciais = (a.nome || '--').split(' ')
            .filter(Boolean)
            .slice(0, 2)
            .map(p => p[0])
            .join('')
            .toUpperCase();
        return `
        <div class="ca-agente-item" id="agente-item-${a.id}">
            <div class="ca-agente-item__info">
                <div class="ca-agente-avatar">${iniciais}</div>
                <div>
                    <span class="ca-agente-nome">${escapeHtml(a.nome)}</span>
                    <span class="ca-agente-status">${escapeHtml(a.perfil || '')}</span>
                </div>
            </div>
            <div class="ca-agente-item__actions">
                <button class="ca-btn-desvincular"
                        onclick="desvincularAgente(${a.id})">
                    Desvincular
                </button>
            </div>
        </div>`;
    }).join('');
}

function vincularAgente() {
    const sel     = document.getElementById('selectNovoAgente');
    const agenteId = sel.value;
    if (!agenteId) return;

    fetch(`/campanhas/admin/${_campanhaId}/agentes/vincular/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ agente_id: agenteId })
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(() => {
        _mostrarFeedback('✓ Agente vinculado com sucesso!', 'success');
        // Remove do select e recarrega lista
        sel.querySelector(`option[value="${agenteId}"]`)?.remove();
        sel.value = '';
        _carregarAgentes(_campanhaId);
    })
    .catch(err => {
        const msg = err?.messages?.agente?.__all__?.[0] || 'Erro ao vincular agente.';
        _mostrarFeedback(msg, 'error');
    });
}

function desvincularAgente(agenteId) {
    fetch(`/campanhas/admin/${_campanhaId}/agentes/${agenteId}/desvincular/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(() => {
        _mostrarFeedback('Agente desvinculado.', 'success');
        _carregarAgentes(_campanhaId);
    })
    .catch(err => {
        const msg = err?.messages?.agente?.__all__?.[0] || 'Erro ao desvincular.';
        _mostrarFeedback(msg, 'error');
    });
}


// ════════════════════════════════════════════════════════════
// MAILING — busca individual + importação CSV
// ════════════════════════════════════════════════════════════

function _carregarMailing(campanhaId) {
    document.getElementById('caSpinner').style.display     = 'none';
    document.getElementById('painelMailing').style.display = 'block';
    _carregarResumoCampanha(campanhaId);
}

function setMailingMode(mode) {
    document.getElementById('modoBusca').style.display = mode === 'busca' ? 'block' : 'none';
    document.getElementById('modoCsv').style.display   = mode === 'csv'   ? 'block' : 'none';
    document.getElementById('tabBusca').classList.toggle('active', mode === 'busca');
    document.getElementById('tabCsv').classList.toggle('active',   mode === 'csv');
    document.getElementById('resultadoBuscaMailing').innerHTML = '';
}

function setSearchField(btn) {
    document.querySelectorAll('.ca-search-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    _searchField = btn.dataset.field;

    const placeholders = {
        documento: 'Digite o CPF do cliente...',
        nome:      'Digite o nome do cliente...',
        telefone:  'Digite o telefone do cliente...',
    };
    document.getElementById('inputBuscaCliente').placeholder = placeholders[_searchField];
    document.getElementById('resultadoBuscaMailing').innerHTML = '';
}

function buscarClienteMailing() {
    const valor = document.getElementById('inputBuscaCliente').value.trim();
    if (!valor) return;

    const container = document.getElementById('resultadoBuscaMailing');
    container.innerHTML = '<div style="text-align:center; padding:16px"><div class="ca-spinner" style="margin:auto"></div></div>';

    fetch('/clientes/search_cliente', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ [_searchField]: valor, modo: 'search' })
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(data => _renderizarResultadosBusca(data.data || []))
    .catch(err => {
        const msg = err?.messages?.cliente?.error?.[0] || 'Cliente não encontrado.';
        container.innerHTML = `<p style="color:#c33; font-size:13px; padding:10px 0">${msg}</p>`;
    });
}

function _renderizarResultadosBusca(clientes) {
    const container = document.getElementById('resultadoBuscaMailing');
    if (!clientes.length) {
        container.innerHTML = '<p style="color:#aaa; font-size:13px; padding:10px 0">Nenhum cliente encontrado.</p>';
        return;
    }

    container.innerHTML = clientes.map(c => {
        const temAgenda = c.tem_agenda && c.agentes.length > 0;
        const badgeHtml = temAgenda
            ? `<span class="ca-resultado-badge ca-resultado-badge--vinculado">Em atendimento</span>`
            : `<span class="ca-resultado-badge ca-resultado-badge--livre">Disponível</span>`;

        return `
        <div class="ca-resultado-item">
            <div class="ca-resultado-info">
                <span class="ca-resultado-nome">${escapeHtml(c.nome)}</span>
                <span class="ca-resultado-doc">${escapeHtml(c.documento)}</span>
                ${badgeHtml}
            </div>
            <button class="ca-btn-vincular-cliente"
                    onclick="adicionarClienteMailing(${c.id}, '${escapeHtml(c.nome)}', this)">
                Adicionar →
            </button>
        </div>`;
    }).join('');
}

function adicionarClienteMailing(clienteId, clienteNome, btn) {
    btn.disabled      = true;
    btn.textContent   = 'Adicionando...';

    fetch(`/campanhas/admin/${_campanhaId}/mailing/adicionar/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cliente_id: clienteId })
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        btn.textContent = '✓ Adicionado';
        btn.style.background = '#1e8449';
        _mostrarFeedback(`✓ ${escapeHtml(clienteNome)} adicionado ao mailing!`, 'success');
        _carregarResumoCampanha(_campanhaId);
    })
    .catch(err => {
        btn.disabled    = false;
        btn.textContent = 'Adicionar →';
        const msg = err?.messages?.mailing?.__all__?.[0] || 'Erro ao adicionar cliente.';
        _mostrarFeedback(msg, 'error');
    });
}

// ── CSV ──────────────────────────────────────────────────────
function handleCsvDrop(event) {
    event.preventDefault();
    document.getElementById('csvDrop').classList.remove('ca-csv-drop--over');
    const file = event.dataTransfer.files[0];
    if (file) _processarCsv(file);
}

function handleCsvFile(input) {
    if (input.files[0]) _processarCsv(input.files[0]);
}

function _processarCsv(file) {
    document.getElementById('csvFileName').textContent = file.name;
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        _csvData = _parseCsv(text);
        _renderizarPreviewCsv(_csvData.slice(0, 5));
        document.getElementById('btnImportarCsv').style.display =
            _csvData.length ? 'inline-flex' : 'none';
    };
    reader.readAsText(file);
}

function _parseCsv(text) {
    const linhas = text.trim().split('\n');
    if (linhas.length < 2) return [];

    const headers = linhas[0].split(',').map(h => h.trim().toLowerCase().replace(/"/g, ''));
    const docIdx  = headers.indexOf('documento');

    if (docIdx === -1) {
        _mostrarFeedback('CSV inválido: coluna "documento" não encontrada.', 'error');
        return [];
    }

    return linhas.slice(1).map(linha => {
        const cols = linha.split(',').map(c => c.trim().replace(/"/g, ''));
        const obj  = {};
        headers.forEach((h, i) => { obj[h] = cols[i] || ''; });
        return obj;
    }).filter(r => r.documento);
}

function _renderizarPreviewCsv(rows) {
    if (!rows.length) { document.getElementById('csvPreview').innerHTML = ''; return; }
    const headers = Object.keys(rows[0]);
    const html = `
        <p style="font-size:12px; color:#888; margin-bottom:6px">
            Prévia (${rows.length} de ${_csvData.length} registros)
        </p>
        <table>
            <thead>
                <tr>${headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${rows.map(r =>
                    `<tr>${headers.map(h => `<td>${escapeHtml(r[h] || '')}</td>`).join('')}</tr>`
                ).join('')}
            </tbody>
        </table>`;
    document.getElementById('csvPreview').innerHTML = html;
}

function importarCsv() {
    if (!_csvData.length) return;

    const btn  = document.getElementById('btnImportarCsv');
    btn.disabled    = true;
    btn.innerHTML   = '<div class="ca-spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;margin-right:6px"></div> Importando...';

    fetch(`/campanhas/admin/${_campanhaId}/mailing/importar/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ clientes: _csvData })
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const msg = d.messages?.mailing?.success?.[0] || '✓ Importação concluída!';
        _mostrarFeedback(msg, 'success');
        _csvData = [];
        document.getElementById('csvPreview').innerHTML    = '';
        document.getElementById('csvFileName').textContent = '';
        document.getElementById('csvFile').value           = '';
        btn.style.display = 'none';
        _carregarResumoCampanha(_campanhaId);
    })
    .catch(err => {
        const msg = err?.messages?.mailing?.__all__?.[0] || 'Erro na importação.';
        _mostrarFeedback(msg, 'error');
    })
    .finally(() => {
        btn.disabled  = false;
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M7 2v7M4 6l3 3 3-3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 10v1a1 1 0 001 1h8a1 1 0 001-1v-1" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
        </svg> Importar Clientes`;
    });
}

// ── Resumo do mailing ────────────────────────────────────────
function _carregarResumoCampanha(campanhaId) {
    const container = document.getElementById('resumoMailing');
    container.innerHTML = '<div class="ca-spinner" style="margin:20px auto"></div>';

    fetch(`/campanhas/admin/${campanhaId}/mailing/resumo/`)
        .then(r => r.json())
        .then(data => {
            const cards = [
                { label: 'Total',      num: data.total,    cls: 'total' },
                { label: 'Na Fila',    num: data.inicial,  cls: 'inicial' },
                { label: 'Em Atend.', num: data.curso,    cls: 'curso' },
                { label: 'Agendado',  num: data.agenda,   cls: 'agenda' },
                { label: 'Sucesso',   num: data.sucesso,  cls: 'sucesso' },
                { label: 'Outros',    num: data.outro,    cls: 'outro' },
            ];

            container.innerHTML = cards.map(c => `
                <div class="ca-resumo-card">
                    <span class="ca-resumo-num ca-resumo-num--${c.cls}">${c.num ?? 0}</span>
                    <span class="ca-resumo-label">${c.label}</span>
                </div>`).join('');
        })
        .catch(() => {
            container.innerHTML = '<p style="color:#aaa; font-size:12px">Erro ao carregar resumo.</p>';
        });
}


// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function _resetDrawer() {
    document.getElementById('caSpinner').style.display     = 'flex';
    document.getElementById('formCampanha').style.display  = 'none';
    document.getElementById('painelAgentes').style.display = 'none';
    document.getElementById('painelMailing').style.display = 'none';
    document.getElementById('caFeedback').style.display    = 'none';
    document.getElementById('resultadoBuscaMailing').innerHTML = '';
    document.getElementById('csvPreview').innerHTML        = '';
    document.getElementById('csvFileName').textContent     = '';
    _csvData = [];
    _limparErros();
    // Reset mailing tabs
    setMailingMode('busca');
}

function _limparErros() {
    document.querySelectorAll('.ca-form__error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
    document.querySelectorAll('.ca-form__input--error').forEach(el =>
        el.classList.remove('ca-form__input--error')
    );
}

function _mostrarFeedback(msg, tipo) {
    const el = document.getElementById('caFeedback');
    el.textContent = msg;
    el.className = `ca-drawer__feedback ca-drawer__feedback--${tipo}`;
    el.style.display = 'block';
    // Auto-hide successes
    if (tipo === 'success') {
        setTimeout(() => { el.style.display = 'none'; }, 3000);
    }
}

function _setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}

function _atualizarToggleText(spanId, checked) {
    const el = document.getElementById(spanId);
    if (el) el.textContent = checked ? 'Ativa' : 'Inativa';
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;')
        .replace(/'/g,'&#039;');
}

// Fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharDrawer();
});

// Enter na busca de cliente
document.addEventListener('DOMContentLoaded', () => {
    const inp = document.getElementById('inputBuscaCliente');
    if (inp) {
        inp.addEventListener('keydown', e => {
            if (e.key === 'Enter') buscarClienteMailing();
        });
    }

    const chk = document.getElementById('cp_ativo');
    if (chk) {
        chk.addEventListener('change', () =>
            _atualizarToggleText('cp_ativo_text', chk.checked)
        );
    }
});