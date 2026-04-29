// configuracoes.js — Perfis e Equipes
import { DRAWER_CONFIG } from './drawer/drawer.js';
window.abrirDrawer = abrirDrawer;
window.fecharDrawer = fecharDrawer;
window.salvarDrawer = salvarDrawer;
window.toggleItem = toggleItem;


// ── Estado ──────────────────────────────────────────────────
let _tipo    = null;   // 'perfil' | 'equipe'
let _itemId  = null;   // null = criação, number = edição
let _groupMode = 'existente';  // 'existente' | 'novo'

// ── URLs ─────────────────────────────────────────────────────
const URLS = {
    perfil: (id) => id ? `/usuarios/perfil/${id}/` : '/usuarios/perfil/',
    equipe: (id) => id ? `/usuarios/equipe/${id}/` : '/usuarios/equipe/',
    carteira: (id) => id ? `/usuarios/carteira/${id}/` : '/usuarios/carteira/',
    perfilToggle: (id) => `/usuarios/perfil/${id}/toggle/`,
    equipeToggle: (id) => `/usuarios/equipe/${id}/toggle/`,
    carteiraToggle: (id) => `/usuarios/carteira/${id}/toggle/`,
};


function abrirDrawer(tipo, itemId) {
    _tipo   = tipo;
    _itemId = itemId;

    const cfg = DRAWER_CONFIG[tipo];
    if (!cfg) {
        console.error('Tipo não configurado:', tipo);
        return;
    }

    _resetDrawer();

    const ehNovo = itemId === null;

    // TEXTOS
    document.getElementById('cfgDrawerTitle').textContent =
        ehNovo ? cfg.tituloNovo : cfg.tituloEditar;

    document.getElementById('cfgDrawerSubtitle').textContent =
        ehNovo ? 'Preencha os dados abaixo' : 'Altere os campos desejados';

    // HEADER STYLE
    document.getElementById('cfgDrawerHeader').className =
        `cfg-drawer__header cfg-drawer__header--${tipo}`;

    // ÍCONE
    document.getElementById('cfgDrawerIcon').innerHTML = cfg.icon;

    // BOTÃO
    document.getElementById('cfgBtnLabel').textContent =
        ehNovo ? 'Criar' : 'Salvar';

    // OPEN
    document.getElementById('cfgOverlay').classList.add('active');
    document.getElementById('cfgDrawer').classList.add('active');

    // FETCH
    fetch(URLS[tipo](itemId))
        .then(r => r.json())
        .then(data => _preencherForm(tipo, data))
        .catch(() => _mostrarFeedback('Erro ao carregar dados.', 'error'));
}

// ── Fechar ───────────────────────────────────────────────────
function fecharDrawer() {
    document.getElementById('cfgOverlay').classList.remove('active');
    document.getElementById('cfgDrawer').classList.remove('active');
    _tipo   = null;
    _itemId = null;
}

// ── Preencher formulário ─────────────────────────────────────
function _preencherForm(tipo, data) {
    document.getElementById('cfgSpinner').style.display = 'none';

    if (tipo === 'perfil') {
        const form   = document.getElementById('formPerfil');
        const perfil = data.perfil || {};

        // Preenche selects de choices (já estão no HTML via Django)
        _setVal('pf_codigo', perfil.codigo  || '');
        _setVal('pf_escopo', perfil.escopo  || '');

        // Popular select de groups
        const selGroup = document.getElementById('pf_grupo_id');
        selGroup.innerHTML = '<option value="">Nenhum</option>';
        (data.groups || []).forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.name;
            if (g.id === perfil.grupo_id) opt.selected = true;
            selGroup.appendChild(opt);
        });

        // Toggle de ativo
        const chk = document.getElementById('pf_ativo');
        chk.checked = perfil.ativo !== false;
        _atualizarToggleText('pf_ativo_text', chk.checked, 'Ativo', 'Inativo');
        chk.addEventListener('change', () =>
            _atualizarToggleText('pf_ativo_text', chk.checked, 'Ativo', 'Inativo')
        );

        // Modo group (reset para existente)
        setGroupMode('existente');
        document.getElementById('pf_criar_grupo_nome').value = '';

        form.style.display = 'block';

    }
    if (tipo === 'carteira') {
        const form   = document.getElementById('formCarteira');
        const carteira = data.carteira || {};

        _setVal('ct_nome', carteira.nome || '');

        // Toggle de ativo
        const chk = document.getElementById('ct_ativo');
        chk.checked = carteira.ativo !== false;
        _atualizarToggleText('ct_ativo_text', chk.checked, 'Ativa', 'Inativa');
        chk.addEventListener('change', () =>
            _atualizarToggleText('ct_ativo_text', chk.checked, 'Ativa', 'Inativa')
        );

        form.style.display = 'block';
    }
     else {
        const form   = document.getElementById('formEquipe');
        const equipe = data.equipe || {};

        _setVal('eq_nome', equipe.nome || '');

        // Popular select de responsáveis
        const selResp = document.getElementById('eq_responsavel_id');
        selResp.innerHTML = '<option value="">Nenhum</option>';
        (data.usuarios || []).forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.usuario_id;
            opt.textContent = (u.nome).trim() || u.usuario__username;
            if (u.usuario_id === equipe.responsavel_id) opt.selected = true;
            selResp.appendChild(opt);
        });

        // Toggle de ativo
        const chk = document.getElementById('eq_ativo');
        chk.checked = equipe.ativo !== false;
        _atualizarToggleText('eq_ativo_text', chk.checked, 'Ativa', 'Inativa');
        chk.addEventListener('change', () =>
            _atualizarToggleText('eq_ativo_text', chk.checked, 'Ativa', 'Inativa')
        );

        form.style.display = 'block';
    }
}

// ── Salvar ───────────────────────────────────────────────────
function salvarDrawer() {
    if (!_tipo) return;

    _limparErros();

    const btn   = document.getElementById('cfgBtnSalvar');
    const label = document.getElementById('cfgBtnLabel');

    btn.disabled    = true;
    label.textContent = 'Salvando...';

    const payload = _coletarPayload(_tipo);

    fetch(URLS[_tipo](_itemId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        _mostrarFeedback(
            d.messages?.[_tipo]?.success?.[0] || 'Salvo com sucesso!',
            'success'
        );
        setTimeout(() => { fecharDrawer(); location.reload(); }, 900);
    })
    .catch(err => {
        const msgs = err?.messages?.[_tipo] || {};
        let temCampo = false;

        Object.entries(msgs).forEach(([campo, erros]) => {
            const txt  = Array.isArray(erros) ? erros.join(' ') : erros;
            if (campo === '__all__' || campo === 'success') {
                _mostrarFeedback(txt, campo === 'success' ? 'success' : 'error');
                return;
            }
            const prefixo = _tipo === 'perfil' ? 'err-pf-' : 'err-eq-';
            const errEl = document.getElementById(`${prefixo}${campo}`);
            const inpEl = document.querySelector(`#form${_tipo.charAt(0).toUpperCase()+_tipo.slice(1)} [name="${campo}"]`);
            if (errEl) { errEl.textContent = txt; errEl.style.display = 'block'; }
            if (inpEl) inpEl.classList.add('cfg-form__input--error');
            temCampo = true;
        });

        if (!temCampo && !Object.keys(msgs).length)
            _mostrarFeedback('Erro ao salvar. Tente novamente.', 'error');
    })
    .finally(() => {
        btn.disabled = false;
        label.textContent = _itemId ? 'Salvar' : 'Criar';
    });
}

// ── Toggle ativo/inativo (lista) ─────────────────────────────
function toggleItem(tipo, itemId, btn) {
    const url = URLS[`${tipo}Toggle`](itemId);

    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const row   = document.getElementById(`${tipo}-row-${itemId}`);
        const pill  = row.querySelector('.cfg-status-pill');
        const ativo = d.ativo;

        // Atualiza classe da row
        row.classList.toggle('cfg-list__item--inativo', !ativo);

        // Atualiza pill
        pill.className = `cfg-status-pill ${ativo ? 'cfg-status-pill--ativo' : 'cfg-status-pill--inativo'}`;
        pill.textContent = ativo
            ? (tipo === 'equipe' ? 'Ativa' : 'Ativo')
            : (tipo === 'equipe' ? 'Inativa' : 'Inativo');

        // Troca ícone do botão toggle
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
    .catch(() => alert('Erro ao alterar status.'));
}

// ── Modo de group (Perfil) ───────────────────────────────────
function setGroupMode(mode) {
    _groupMode = mode;
    document.getElementById('modoExistente').style.display = mode === 'existente' ? 'block' : 'none';
    document.getElementById('modoNovo').style.display      = mode === 'novo'      ? 'block' : 'none';
    document.getElementById('tabExistente').classList.toggle('active', mode === 'existente');
    document.getElementById('tabNovo').classList.toggle('active',      mode === 'novo');

    // Limpa o campo que não está em uso
    if (mode === 'existente') document.getElementById('pf_criar_grupo_nome').value = '';
    else document.getElementById('pf_grupo_id').value = '';
}

// ── Helpers ──────────────────────────────────────────────────
function _coletarPayload(tipo) {
    if (tipo === 'perfil') {
        const chk = document.getElementById('pf_ativo');
        return {
            codigo:           document.getElementById('pf_codigo').value,
            escopo:           document.getElementById('pf_escopo').value,
            grupo_id:         _groupMode === 'existente' ? document.getElementById('pf_grupo_id').value : null,
            criar_grupo_nome: _groupMode === 'novo'      ? document.getElementById('pf_criar_grupo_nome').value.trim() : '',
            ativo:            chk.checked,
        };
    }
    if (tipo === 'carteira') {
        const chk = document.getElementById('ct_ativo');
        return {
            nome:           document.getElementById('ct_nome').value.trim(),
            ativo:          chk.checked,
        };
    }
    else {
        const chk = document.getElementById('eq_ativo');
        return {
            nome:           document.getElementById('eq_nome').value.trim(),
            responsavel_id: document.getElementById('eq_responsavel_id').value || null,
            ativo:          chk.checked,
        };
    }
}

function _setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
}

function _atualizarToggleText(spanId, checked, labelOn, labelOff) {
    const el = document.getElementById(spanId);
    if (el) el.textContent = checked ? labelOn : labelOff;
}

function _resetDrawer() {
    document.getElementById('cfgSpinner').style.display       = 'flex';
    document.getElementById('formPerfil').style.display       = 'none';
    document.getElementById('formEquipe').style.display       = 'none';
    document.getElementById('formCarteira').style.display     = 'none';
    document.getElementById('cfgFeedback').style.display      = 'none';
    _limparErros();
}

function _limparErros() {
    document.querySelectorAll('.cfg-form__error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
    document.querySelectorAll('.cfg-form__input--error').forEach(el =>
        el.classList.remove('cfg-form__input--error')
    );
}

function _mostrarFeedback(msg, tipo) {
    const el = document.getElementById('cfgFeedback');
    el.textContent = msg;
    el.className = `cfg-drawer__feedback cfg-drawer__feedback--${tipo}`;
    el.style.display = 'block';
}

// Fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharDrawer();
});