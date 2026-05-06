// situacoes.js — Gestão de Situações

// ── Estado ───────────────────────────────────────────────────
let _situacaoId = null;   // null = criação, number = edição

// ── URLs ─────────────────────────────────────────────────────
const SIT_URLS = {
    situacao:       (id) => id ? `/agenda/situacao/${id}/`        : '/agenda/situacao/',
    situacaoToggle: (id) => `/agenda/situacao/${id}/toggle/`,
};

// ── Abrir drawer ──────────────────────────────────────────────
function abrirDrawer(situacaoId) {
    _situacaoId = situacaoId;

    _resetDrawer();

    const ehNovo = situacaoId === null;

    document.getElementById('sitDrawerTitle').textContent    = ehNovo ? 'Nova Situação' : 'Editar Situação';
    document.getElementById('sitDrawerSubtitle').textContent = ehNovo ? 'Preencha os dados abaixo' : 'Altere os dados da situação';
    document.getElementById('sitBtnLabel').textContent       = ehNovo ? 'Criar' : 'Salvar';

    document.getElementById('sitOverlay').classList.add('active');
    document.getElementById('sitDrawer').classList.add('active');

    fetch(SIT_URLS.situacao(situacaoId))
        .then(r => r.json())
        .then(data => _preencherForm(data))
        .catch(() => _mostrarFeedback('Erro ao carregar dados.', 'error'));
}

// ── Fechar drawer ─────────────────────────────────────────────
function fecharDrawer() {
    document.getElementById('sitOverlay').classList.remove('active');
    document.getElementById('sitDrawer').classList.remove('active');
    _situacaoId = null;
}

// ── Preencher formulário ──────────────────────────────────────
function _preencherForm(data) {
    document.getElementById('sitSpinner').style.display = 'none';
    document.getElementById('sitForm').style.display    = 'block';

    const s = data.situacao || {};
    const tipos = data.tipos;
    _setVal('sit_nome',      s.nome  || '');

    const html = tipos.map(([codigo, nome]) => `
        <option value="${codigo}" ${codigo == s.tipo ? 'selected' : ''}>${nome}</option>
    `).join('');
    document.getElementById('sit_tipo').innerHTML = html;


    // Cor: usa #5E35B1 como padrão se não houver
    const cor = s.cor || '#5E35B1';
    document.getElementById('sit_cor_picker').value = cor;
    document.getElementById('sit_cor_text').value   = cor.toUpperCase();

    const chk = document.getElementById('sit_ativo');
    chk.checked = s.ativo !== false;
    _updateToggleText('sit_ativo_text', chk.checked, 'Ativa', 'Inativa');
}

// ── Salvar ────────────────────────────────────────────────────
function salvarDrawer() {
    _limparErros();

    const btn   = document.getElementById('sitBtnSalvar');
    const label = document.getElementById('sitBtnLabel');
    btn.disabled      = true;
    label.textContent = 'Salvando...';

    const payload = {
        nome:      document.getElementById('sit_nome').value.trim(),
        tipo: document.getElementById('sit_tipo').value.trim(),
        ativo:     document.getElementById('sit_ativo').checked,
    };

    fetch(SIT_URLS.situacao(_situacaoId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const msg = d.messages?.situacao?.success?.[0] || '✓ Situação salva com sucesso!';
        _mostrarFeedback(msg, 'success');
        setTimeout(() => { fecharDrawer(); location.reload(); }, 900);
    })
    .catch(err => {
        const msgs = err?.messages?.situacao || {};
        let temCampo = false;

        Object.entries(msgs).forEach(([campo, erros]) => {
            const txt = Array.isArray(erros) ? erros.join(' ') : erros;
            if (campo === '__all__' || campo === 'success') {
                _mostrarFeedback(txt, campo === 'success' ? 'success' : 'error');
                return;
            }
            const errEl = document.getElementById(`err-sit-${campo}`);
            const inpEl = document.querySelector(`#sitForm [name="${campo}"]`);
            if (errEl) { errEl.textContent = txt; errEl.style.display = 'block'; }
            if (inpEl) inpEl.classList.add('sit-form__input--error');
            temCampo = true;
        });

        if (!temCampo && !Object.keys(msgs).length)
            _mostrarFeedback('Erro ao salvar. Tente novamente.', 'error');
    })
    .finally(() => {
        btn.disabled      = false;
        label.textContent = _situacaoId ? 'Salvar' : 'Criar';
    });
}

// ── Toggle ativo na tabela ────────────────────────────────────
function toggleItem(situacaoId, btn) {
    fetch(SIT_URLS.situacaoToggle(situacaoId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const row   = document.getElementById(`sit-row-${situacaoId}`);
        const pill  = row.querySelector('.sit-status');
        const ativo = d.ativo;

        row.classList.toggle('sit-row--inativa', !ativo);

        pill.className   = `sit-status sit-status--${ativo ? 'ativa' : 'inativa'}`;
        pill.textContent = ativo ? 'Ativa' : 'Inativa';

        btn.innerHTML = ativo
            ? `<svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                   <rect x="2" y="2" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.4"/>
                   <path d="M4 7h6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
               </svg>`
            : `<svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                   <rect x="2" y="2" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.4"/>
                   <path d="M4 7l2.5 2.5L10 4.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
               </svg>`;

        // Atualiza contadores
        _atualizarContadores();
    })
    .catch(() => alert('Erro ao alterar status.'));
}

// ── Sincronização do color picker ────────────────────────────
function syncColorFromPicker(picker) {
    const val = picker.value.toUpperCase();
    document.getElementById('sit_cor_text').value = val;
}

function syncColorFromText(input) {
    const val = input.value.trim();
    // Aceita formato #RRGGBB
    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
        document.getElementById('sit_cor_picker').value = val;
    }
    input.value = val.toUpperCase();
}

// ── Atualizar contadores ──────────────────────────────────────
function _atualizarContadores() {
    const rows    = document.querySelectorAll('.sit-row');
    const inativas = document.querySelectorAll('.sit-row--inativa').length;
    const ativas   = rows.length - inativas;

    const el = (id) => document.getElementById(id);
    if (el('sitCntTotal'))   el('sitCntTotal').textContent   = rows.length;
    if (el('sitCntAtivas'))  el('sitCntAtivas').textContent  = ativas;
    if (el('sitCntInativas'))el('sitCntInativas').textContent = inativas;
}

// ── Helpers ───────────────────────────────────────────────────
function _setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}

function _updateToggleText(spanId, checked, labelOn, labelOff) {
    const el = document.getElementById(spanId);
    if (el) el.textContent = checked ? labelOn : labelOff;
}

function _resetDrawer() {
    document.getElementById('sitSpinner').style.display = 'flex';
    document.getElementById('sitForm').style.display    = 'none';
    document.getElementById('sitFeedback').style.display = 'none';
    _limparErros();
}

function _limparErros() {
    document.querySelectorAll('.sit-form__error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
    document.querySelectorAll('.sit-form__input--error').forEach(el =>
        el.classList.remove('sit-form__input--error')
    );
}

function _mostrarFeedback(msg, tipo) {
    const el = document.getElementById('sitFeedback');
    el.textContent = msg;
    el.className   = `sit-drawer__feedback sit-drawer__feedback--${tipo}`;
    el.style.display = 'block';
    if (tipo === 'success') {
        setTimeout(() => { el.style.display = 'none'; }, 3000);
    }
}

// ── Listeners ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const chk = document.getElementById('sit_ativo');
    if (chk) {
        chk.addEventListener('change', () =>
            _updateToggleText('sit_ativo_text', chk.checked, 'Ativa', 'Inativa')
        );
    }
});

// Fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharDrawer();
});