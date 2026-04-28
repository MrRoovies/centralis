// vendas_admin.js — Gestão de Parceiros, Produtos, Ofertas e Esteiras

// ── Estado global ────────────────────────────────────────────
let _tipo   = null;   // 'parceiro' | 'produto' | 'oferta' | 'esteira'
let _itemId = null;   // null = criação, number = edição

// ── URLs ─────────────────────────────────────────────────────
const VA_URLS = {
    parceiro: (id) => id ? `/vendas/admin/parceiro/${id}/` : '/vendas/admin/parceiro/',
    produto:  (id) => id ? `/vendas/admin/produto/${id}/`  : '/vendas/admin/produto/',
    oferta:   (id) => id ? `/vendas/admin/oferta/${id}/`   : '/vendas/admin/oferta/',
    esteira:  (id) => id ? `/vendas/admin/esteira/${id}/`  : '/vendas/admin/esteira/',
    toggleParceiro: (id) => `/vendas/admin/parceiro/${id}/toggle/`,
    toggleProduto:  (id) => `/vendas/admin/produto/${id}/toggle/`,
    toggleOferta:   (id) => `/vendas/admin/oferta/${id}/toggle/`,
    toggleEsteira:  (id) => `/vendas/admin/esteira/${id}/toggle/`,
};

// ── Navegação por tabs ────────────────────────────────────────
function setTab(tabName) {
    document.querySelectorAll('.va-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.va-panel').forEach(p => p.classList.remove('active'));

    document.querySelector(`.va-tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`panel-${tabName}`).classList.add('active');
}

// ── Abrir drawer ──────────────────────────────────────────────
function abrirDrawer(tipo, itemId) {
    _tipo   = tipo;
    _itemId = itemId;

    _resetDrawer();

    const ehNovo = itemId === null;

    const configs = {
        parceiro: {
            title:    ehNovo ? 'Novo Parceiro' : 'Editar Parceiro',
            subtitle: ehNovo ? 'Cadastre um novo parceiro' : 'Altere os dados do parceiro',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <rect x="2" y="5" width="16" height="12" rx="2" stroke="white" stroke-width="1.6"/>
                       <path d="M6 5V4a2 2 0 012-2h4a2 2 0 012 2v1" stroke="white" stroke-width="1.6"/>
                       <path d="M10 10v4M8 12h4" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
                   </svg>`,
        },
        produto: {
            title:    ehNovo ? 'Novo Produto' : 'Editar Produto',
            subtitle: ehNovo ? 'Cadastre um novo produto' : 'Altere os dados do produto',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <path d="M10 2L2 6v8l8 4 8-4V6l-8-4z" stroke="white" stroke-width="1.6" stroke-linejoin="round"/>
                       <path d="M2 6l8 4m0 0l8-4m-8 4v8" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
                   </svg>`,
        },
        oferta: {
            title:    ehNovo ? 'Nova Oferta' : 'Editar Oferta',
            subtitle: ehNovo ? 'Crie uma nova oferta comercial' : 'Altere os dados da oferta',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <circle cx="10" cy="10" r="8" stroke="white" stroke-width="1.6"/>
                       <path d="M10 6v8M7 8.5h4.5a1.5 1.5 0 010 3H9a1.5 1.5 0 010 3H13" stroke="white" stroke-width="1.4" stroke-linecap="round"/>
                   </svg>`,
        },
        esteira: {
            title:    ehNovo ? 'Nova Esteira' : 'Editar Esteira',
            subtitle: ehNovo ? 'Crie uma etapa do funil de vendas' : 'Altere os dados da esteira',
            icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                       <path d="M3 5h14M5 10h10M7 15h6" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
                   </svg>`,
        },
    };

    const cfg = configs[tipo];
    document.getElementById('vaDrawerTitle').textContent    = cfg.title;
    document.getElementById('vaDrawerSubtitle').textContent = cfg.subtitle;
    document.getElementById('vaDrawerIcon').innerHTML       = cfg.icon;
    document.getElementById('vaDrawerHeader').className =
        `va-drawer__header va-drawer__header--${tipo}`;
    document.getElementById('vaBtnLabel').textContent = ehNovo ? 'Criar' : 'Salvar';

    document.getElementById('vaOverlay').classList.add('active');
    document.getElementById('vaDrawer').classList.add('active');

    // Carrega dados via GET
    fetch(VA_URLS[tipo](itemId))
        .then(r => r.json())
        .then(data => _preencherForm(tipo, data))
        .catch(() => _mostrarFeedback('Erro ao carregar dados.', 'error'));
}

// ── Fechar drawer ─────────────────────────────────────────────
function fecharDrawer() {
    document.getElementById('vaOverlay').classList.remove('active');
    document.getElementById('vaDrawer').classList.remove('active');
    _tipo   = null;
    _itemId = null;
}

// ── Preencher formulário ──────────────────────────────────────
function _preencherForm(tipo, data) {
    document.getElementById('vaSpinner').style.display = 'none';

    // Oculta todos os forms e exibe o correto
    document.querySelectorAll('.va-form-content').forEach(f => f.style.display = 'none');
    document.getElementById(`form-${tipo}`).style.display = 'block';

    if (tipo === 'parceiro') {
        const p = data.parceiro || {};
        _setVal('pa_nome', p.nome || '');
        _toggleSwitch('pa_ativo', p.ativo !== false);
        _updateToggleText('pa_ativo_text', p.ativo !== false, 'Ativo', 'Inativo');
    }

    if (tipo === 'produto') {
        const p = data.produto || {};
        _setVal('pr_nome', p.nome || '');
        _toggleSwitch('pr_ativo', p.ativo !== false);
        _updateToggleText('pr_ativo_text', p.ativo !== false, 'Ativo', 'Inativo');
    }

    if (tipo === 'oferta') {
        const o = data.oferta || {};

        // Popula selects
        const selParceiro = document.getElementById('of_parceiro');
        selParceiro.innerHTML = '<option value="">Selecione...</option>';
        (data.parceiros || []).forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.nome;
            if (p.id === o.parceiro_id) opt.selected = true;
            selParceiro.appendChild(opt);
        });

        const selProduto = document.getElementById('of_produto');
        selProduto.innerHTML = '<option value="">Selecione...</option>';
        (data.produtos || []).forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.nome;
            if (p.id === o.produto_id) opt.selected = true;
            selProduto.appendChild(opt);
        });

        _setVal('of_prazo_min', o.prazo_min ?? '');
        _setVal('of_prazo_max', o.prazo_max ?? '');
        _setVal('of_comissao', o.comissao ?? '');
        _toggleSwitch('of_ativo', o.ativo !== false);
        _updateToggleText('of_ativo_text', o.ativo !== false, 'Ativa', 'Inativa');
        _atualizarPreviewComissao();
    }

    if (tipo === 'esteira') {
        const e = data.esteira || {};

        // Popula select de carteiras
        const selCarteira = document.getElementById('es_carteira');
        selCarteira.innerHTML = '<option value="">Selecione...</option>';
        (data.carteiras || []).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.nome;
            if (c.id === e.carteira_id) opt.selected = true;
            selCarteira.appendChild(opt);
        });

        _setVal('es_nome',  e.nome  || '');
        _setVal('es_tipo',  e.tipo  || '');
        _setVal('es_ordem', e.ordem ?? 1);
        _toggleSwitch('es_ativo', e.ativo !== false);
        _updateToggleText('es_ativo_text', e.ativo !== false, 'Ativa', 'Inativa');
    }
}

// ── Salvar ────────────────────────────────────────────────────
function salvarDrawer() {
    if (!_tipo) return;

    _limparErros();

    const btn   = document.getElementById('vaBtnSalvar');
    const label = document.getElementById('vaBtnLabel');
    btn.disabled      = true;
    label.textContent = 'Salvando...';

    const payload = _coletarPayload(_tipo);

    fetch(VA_URLS[_tipo](_itemId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const msg = d.messages?.[_tipo]?.success?.[0] || '✓ Salvo com sucesso!';
        _mostrarFeedback(msg, 'success');
        setTimeout(() => { fecharDrawer(); location.reload(); }, 900);
    })
    .catch(err => {
        const msgs = err?.messages?.[_tipo] || {};
        let temCampo = false;

        Object.entries(msgs).forEach(([campo, erros]) => {
            const txt = Array.isArray(erros) ? erros.join(' ') : erros;
            if (campo === '__all__' || campo === 'success') {
                _mostrarFeedback(txt, campo === 'success' ? 'success' : 'error');
                return;
            }
            const prefixMap = { parceiro: 'pa', produto: 'pr', oferta: 'of', esteira: 'es' };
            const prefixo = prefixMap[_tipo];
            const errEl = document.getElementById(`err-${prefixo}-${campo}`);
            const inpEl = document.querySelector(`#form-${_tipo} [name="${campo}"]`);
            if (errEl) { errEl.textContent = txt; errEl.style.display = 'block'; }
            if (inpEl) inpEl.classList.add('va-form__input--error');
            temCampo = true;
        });

        if (!temCampo && !Object.keys(msgs).length) {
            _mostrarFeedback('Erro ao salvar. Tente novamente.', 'error');
        }
    })
    .finally(() => {
        btn.disabled      = false;
        label.textContent = _itemId ? 'Salvar' : 'Criar';
    });
}

// ── Toggle ativo na tabela ────────────────────────────────────
function toggleItem(tipo, itemId, btn) {
    const urlMap = {
        parceiro: VA_URLS.toggleParceiro,
        produto:  VA_URLS.toggleProduto,
        oferta:   VA_URLS.toggleOferta,
        esteira:  VA_URLS.toggleEsteira,
    };

    fetch(urlMap[tipo](itemId), {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const row   = document.getElementById(`${tipo}-row-${itemId}`);
        const pill  = row.querySelector('.va-status');
        const ativo = d.ativo;

        row.classList.toggle('va-row--inativo', !ativo);

        pill.className = `va-status va-status--${ativo ? 'ativo' : 'inativo'}`;
        pill.textContent = ativo ? 'Ativo' : 'Inativo';

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

// ── Preview de comissão ───────────────────────────────────────
function _atualizarPreviewComissao() {
    const comissao = parseFloat(document.getElementById('of_comissao')?.value) || 0;
    const el = document.getElementById('ofComissaoPreview');
    if (el) el.textContent = comissao.toFixed(2) + '%';
}

// ── Stepper de ordem ──────────────────────────────────────────
function stepOrdem(delta) {
    const input = document.getElementById('es_ordem');
    const val = parseInt(input.value || '1') + delta;
    input.value = Math.max(1, val);
}

// ── Helpers ───────────────────────────────────────────────────
function _coletarPayload(tipo) {
    if (tipo === 'parceiro') {
        return {
            nome:  document.getElementById('pa_nome').value.trim(),
            ativo: document.getElementById('pa_ativo').checked,
        };
    }

    if (tipo === 'produto') {
        return {
            nome:  document.getElementById('pr_nome').value.trim(),
            ativo: document.getElementById('pr_ativo').checked,
        };
    }

    if (tipo === 'oferta') {
        return {
            parceiro_id: document.getElementById('of_parceiro').value,
            produto_id:  document.getElementById('of_produto').value,
            prazo_min:   document.getElementById('of_prazo_min').value,
            prazo_max:   document.getElementById('of_prazo_max').value,
            comissao:    document.getElementById('of_comissao').value,
            ativo:       document.getElementById('of_ativo').checked,
        };
    }

    if (tipo === 'esteira') {
        return {
            nome:        document.getElementById('es_nome').value.trim(),
            carteira_id: document.getElementById('es_carteira').value,
            tipo:        document.getElementById('es_tipo').value,
            ordem:       document.getElementById('es_ordem').value,
            ativo:       document.getElementById('es_ativo').checked,
        };
    }
}

function _setVal(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}

function _toggleSwitch(id, checked) {
    const el = document.getElementById(id);
    if (el) el.checked = checked;
}

function _updateToggleText(spanId, checked, labelOn, labelOff) {
    const el = document.getElementById(spanId);
    if (el) el.textContent = checked ? labelOn : labelOff;
}

function _resetDrawer() {
    document.getElementById('vaSpinner').style.display = 'flex';
    document.querySelectorAll('.va-form-content').forEach(f => f.style.display = 'none');
    document.getElementById('vaFeedback').style.display = 'none';
    _limparErros();
}

function _limparErros() {
    document.querySelectorAll('.va-form__error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
    document.querySelectorAll('.va-form__input--error').forEach(el =>
        el.classList.remove('va-form__input--error')
    );
}

function _mostrarFeedback(msg, tipo) {
    const el = document.getElementById('vaFeedback');
    el.textContent = msg;
    el.className = `va-drawer__feedback va-drawer__feedback--${tipo}`;
    el.style.display = 'block';
}

// ── Listeners ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Toggle texts
    ['pa_ativo', 'pr_ativo', 'of_ativo', 'es_ativo'].forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        const textMap = {
            pa_ativo: ['Ativo', 'Inativo'],
            pr_ativo: ['Ativo', 'Inativo'],
            of_ativo: ['Ativa', 'Inativa'],
            es_ativo: ['Ativa', 'Inativa'],
        };
        el.addEventListener('change', () => {
            const [on, off] = textMap[id];
            _updateToggleText(`${id}_text`, el.checked, on, off);
        });
    });

    // Preview comissão em tempo real
    const comissaoInput = document.getElementById('of_comissao');
    if (comissaoInput) {
        comissaoInput.addEventListener('input', _atualizarPreviewComissao);
    }
});

// Fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharDrawer();
});