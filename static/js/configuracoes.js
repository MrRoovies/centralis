// configuracoes.js — Carteiras, Perfis e Equipes
import { DRAWER_CONFIG } from './drawer/drawer.js';

window.abrirDrawer  = abrirDrawer;
window.fecharDrawer = fecharDrawer;
window.salvarDrawer = salvarDrawer;
window.toggleItem   = toggleItem;
window.setTab       = setTab;
window.setGroupMode = setGroupMode;

// ── Estado ───────────────────────────────────────────────────
let _tipo      = null;       // 'carteira' | 'perfil' | 'equipe'
let _itemId    = null;       // null = criação, number = edição
let _groupMode = 'existente';

// ── URLs ─────────────────────────────────────────────────────
const URLS = {
    carteira:       (id) => id ? `/usuarios/carteira/${id}/`        : '/usuarios/carteira/',
    perfil:         (id) => id ? `/usuarios/perfil/${id}/`          : '/usuarios/perfil/',
    equipe:         (id) => id ? `/usuarios/equipe/${id}/`          : '/usuarios/equipe/',
    carteiraToggle: (id) => `/usuarios/carteira/${id}/toggle/`,
    perfilToggle:   (id) => `/usuarios/perfil/${id}/toggle/`,
    equipeToggle:   (id) => `/usuarios/equipe/${id}/toggle/`,
};

// ── Navegação por tabs ────────────────────────────────────────
function setTab(tabName) {
    document.querySelectorAll('.cfg-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.cfg-panel').forEach(p => p.classList.remove('active'));

    document.querySelector(`.cfg-tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`panel-${tabName}`).classList.add('active');
}

// ── Abrir drawer ──────────────────────────────────────────────
function abrirDrawer(tipo, itemId) {
    _tipo   = tipo;
    _itemId = itemId;

    _resetDrawer();

    const ehNovo = itemId === null;

    // Config de cada tipo
    const configs = {
        carteira: {
            title:    ehNovo ? 'Nova Carteira'      : 'Editar Carteira',
            subtitle: ehNovo ? 'Preencha os dados'  : 'Altere os dados da carteira',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <rect x="2" y="5" width="16" height="12" rx="2" stroke="white" stroke-width="1.6"/>
                       <path d="M12 9h6v4h-6a2 2 0 010-4z" stroke="white" stroke-width="1.4" stroke-linejoin="round"/>
                       <circle cx="15.5" cy="11" r="1" fill="white"/>
                   </svg>`,
        },
        perfil: {
            title:    ehNovo ? 'Novo Perfil'        : 'Editar Perfil',
            subtitle: ehNovo ? 'Preencha os dados'  : 'Altere os dados do perfil',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <circle cx="10" cy="7" r="3.5" stroke="white" stroke-width="1.6"/>
                       <path d="M3 18c0-3.866 3.134-7 7-7s7 3.134 7 7"
                             stroke="white" stroke-width="1.6" stroke-linecap="round"/>
                   </svg>`,
        },
        equipe: {
            title:    ehNovo ? 'Nova Equipe'        : 'Editar Equipe',
            subtitle: ehNovo ? 'Preencha os dados'  : 'Altere os dados da equipe',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <circle cx="7" cy="7" r="3" stroke="white" stroke-width="1.6"/>
                       <circle cx="14" cy="7" r="3" stroke="white" stroke-width="1.6"/>
                       <path d="M1 17c0-3.314 2.686-6 6-6"
                             stroke="white" stroke-width="1.6" stroke-linecap="round"/>
                       <path d="M11 17c0-3.314 2.686-6 6-6"
                             stroke="white" stroke-width="1.6" stroke-linecap="round"/>
                   </svg>`,
        },
    };

    const cfg = configs[tipo];

    document.getElementById('cfgDrawerTitle').textContent    = cfg.title;
    document.getElementById('cfgDrawerSubtitle').textContent = cfg.subtitle;
    document.getElementById('cfgDrawerIcon').innerHTML       = cfg.icon;
    document.getElementById('cfgDrawerHeader').className =
        `cfg-drawer__header cfg-drawer__header--${tipo}`;
    document.getElementById('cfgBtnLabel').textContent = ehNovo ? 'Criar' : 'Salvar';

    document.getElementById('cfgOverlay').classList.add('active');
    document.getElementById('cfgDrawer').classList.add('active');

    // Carrega dados via GET
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

// ── Preencher formulário ──────────────────────────────────────
function _preencherForm(tipo, data) {
    document.getElementById('cfgSpinner').style.display = 'none';

    // Oculta todos os forms, exibe o correto
    document.querySelectorAll('.cfg-form-content').forEach(f => f.style.display = 'none');
    document.getElementById(`form-${tipo}`).style.display = 'block';

    if (tipo === 'carteira') {
        const carteira = data.carteira || {};
        _setVal('ct_nome', carteira.nome || '');

        const situacoes = data.carteira.situacoes;

        const html = situacoes.map(sit => `
            <div class="cfg-toggle-sits">
                <input type="checkbox" value="${sit.id}" id="sit_ativo_${sit.id}" ${sit.ativo_carteira} name="sit_ativo" class="cfg-toggle-input">
                <label class="cfg-toggle-label" for="sit_ativo_${sit.id}">
                    <span class="cfg-toggle-knob"></span>
                </label>
                <span class="cfg-toggle-text">${sit.nome}</span>
            </div>
        `).join('');
        document.getElementById('situacoes').innerHTML = html;

        const chk = document.getElementById('ct_ativo');
        chk.checked = carteira.ativo !== false;
        _updateToggleText('ct_ativo_text', chk.checked, 'Ativa', 'Inativa');
    }

    if (tipo === 'perfil') {
        const perfil = data.perfil || {};
        _setVal('pf_codigo', perfil.codigo || '');
        _setVal('pf_escopo', perfil.escopo || '');

        // Popular select de groups
        const selGroup = document.getElementById('pf_grupo_id');
        selGroup.innerHTML = '<option value="">Nenhum (sem permissões de group)</option>';
        (data.groups || []).forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.name;
            if (g.id === perfil.grupo_id) opt.selected = true;
            selGroup.appendChild(opt);
        });

        const chk = document.getElementById('pf_ativo');
        chk.checked = perfil.ativo !== false;
        _updateToggleText('pf_ativo_text', chk.checked, 'Ativo', 'Inativo');

        // Reset group mode
        setGroupMode('existente');
        document.getElementById('pf_criar_grupo_nome').value = '';
    }

    if (tipo === 'equipe') {
        const equipe = data.equipe || {};
        _setVal('eq_nome', equipe.nome || '');

        // Popular select de responsáveis
        const selResp = document.getElementById('eq_responsavel_id');
        selResp.innerHTML = '<option value="">Nenhum</option>';
        (data.usuarios || []).forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.usuario_id;
            opt.textContent = (u.nome || '').trim() || u.usuario__username;
            if (u.usuario_id === equipe.responsavel_id) opt.selected = true;
            selResp.appendChild(opt);
        });

        const chk = document.getElementById('eq_ativo');
        chk.checked = equipe.ativo !== false;
        _updateToggleText('eq_ativo_text', chk.checked, 'Ativa', 'Inativa');
    }
}

// ── Salvar ───────────────────────────────────────────────────
function salvarDrawer() {
    if (!_tipo) return;

    _limparErros();

    const btn   = document.getElementById('cfgBtnSalvar');
    const label = document.getElementById('cfgBtnLabel');
    btn.disabled      = true;
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
            d.messages?.[_tipo]?.success?.[0] || '✓ Salvo com sucesso!',
            'success'
        );
        setTimeout(() => { fecharDrawer(); location.reload(); }, 900);
    })
    .catch(err => {
        const msgs = err?.messages?.[_tipo] || {};
        let temCampo = false;

        const prefixMap = { carteira: 'ct', perfil: 'pf', equipe: 'eq' };
        const prefixo = prefixMap[_tipo];

        Object.entries(msgs).forEach(([campo, erros]) => {
            const txt = Array.isArray(erros) ? erros.join(' ') : erros;
            if (campo === '__all__' || campo === 'success') {
                _mostrarFeedback(txt, campo === 'success' ? 'success' : 'error');
                return;
            }
            const errEl = document.getElementById(`err-${prefixo}-${campo}`);
            const inpEl = document.querySelector(`#form-${_tipo} [name="${campo}"]`);
            if (errEl) { errEl.textContent = txt; errEl.style.display = 'block'; }
            if (inpEl) inpEl.classList.add('cfg-form__input--error');
            temCampo = true;
        });

        if (!temCampo && !Object.keys(msgs).length)
            _mostrarFeedback('Erro ao salvar. Tente novamente.', 'error');
    })
    .finally(() => {
        btn.disabled      = false;
        label.textContent = _itemId ? 'Salvar' : 'Criar';
    });
}

// ── Toggle ativo/inativo na tabela ───────────────────────────
function toggleItem(tipo, itemId, btn) {
    const urlMap = {
        carteira: URLS.carteiraToggle,
        perfil:   URLS.perfilToggle,
        equipe:   URLS.equipeToggle,
    };

    fetch(urlMap[tipo](itemId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const row   = document.getElementById(`${tipo}-row-${itemId}`);
        const pill  = row.querySelector('.cfg-status');
        const ativo = d.ativo;

        row.classList.toggle('cfg-row--inativo', !ativo);

        // Feminino para carteira/equipe, masculino para perfil
        const labelOn  = tipo === 'perfil' ? 'Ativo'  : 'Ativa';
        const labelOff = tipo === 'perfil' ? 'Inativo' : 'Inativa';

        pill.className = `cfg-status cfg-status--${ativo ? 'ativo' : 'inativo'}`;
        pill.textContent = ativo ? labelOn : labelOff;

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

// ── Modo de group (Perfil) ────────────────────────────────────
function setGroupMode(mode) {
    _groupMode = mode;
    document.getElementById('modoExistente').style.display = mode === 'existente' ? 'block' : 'none';
    document.getElementById('modoNovo').style.display      = mode === 'novo'      ? 'block' : 'none';
    document.getElementById('tabExistente').classList.toggle('active', mode === 'existente');
    document.getElementById('tabNovo').classList.toggle('active',      mode === 'novo');

    if (mode === 'existente') document.getElementById('pf_criar_grupo_nome').value = '';
    else                      document.getElementById('pf_grupo_id').value = '';
}

// ── Helpers ───────────────────────────────────────────────────
function _coletarPayload(tipo) {
    if (tipo === 'carteira') {

        const list_sits = Array.from(
            document.querySelectorAll('input[name="sit_ativo"]:checked')
        ).map(el => el.value);

        return {
            nome:  document.getElementById('ct_nome').value.trim(),
            ativo: document.getElementById('ct_ativo').checked,
            situacoes: list_sits
        };
    }
    if (tipo === 'perfil') {
        return {
            codigo:           document.getElementById('pf_codigo').value,
            escopo:           document.getElementById('pf_escopo').value,
            grupo_id:         _groupMode === 'existente' ? document.getElementById('pf_grupo_id').value : null,
            criar_grupo_nome: _groupMode === 'novo'      ? document.getElementById('pf_criar_grupo_nome').value.trim() : '',
            ativo:            document.getElementById('pf_ativo').checked,
        };
    }
    if (tipo === 'equipe') {
        return {
            nome:           document.getElementById('eq_nome').value.trim(),
            responsavel_id: document.getElementById('eq_responsavel_id').value || null,
            ativo:          document.getElementById('eq_ativo').checked,
        };
    }
}

function _setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}

function _updateToggleText(spanId, checked, labelOn, labelOff) {
    const el = document.getElementById(spanId);
    if (el) el.textContent = checked ? labelOn : labelOff;
}

function _resetDrawer() {
    document.getElementById('cfgSpinner').style.display = 'flex';
    document.querySelectorAll('.cfg-form-content').forEach(f => f.style.display = 'none');
    document.getElementById('cfgFeedback').style.display = 'none';
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
    if (tipo === 'success') {
        setTimeout(() => { el.style.display = 'none'; }, 3000);
    }
}

// Fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharDrawer();
});

// Toggle texts reativos
document.addEventListener('DOMContentLoaded', () => {
    const toggles = [
        { id: 'ct_ativo', textId: 'ct_ativo_text', on: 'Ativa',  off: 'Inativa' },
        { id: 'pf_ativo', textId: 'pf_ativo_text', on: 'Ativo',  off: 'Inativo' },
        { id: 'eq_ativo', textId: 'eq_ativo_text', on: 'Ativa',  off: 'Inativa' },
    ];
    toggles.forEach(({ id, textId, on, off }) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => _updateToggleText(textId, el.checked, on, off));
    });
});