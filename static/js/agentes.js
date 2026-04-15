// ── Dados carregados do backend ──────────────────────────────
let dadosModal = null;

function abrirModalNovoAgente() {
    document.getElementById('agModalOverlay').classList.add('active');
    limparModal();

    if (dadosModal) {
        preencherSelects(dadosModal);
        return;
    }

    fetch('/usuarios/novo_agente/')
        .then(r => r.json())
        .then(data => {
            dadosModal = data;
            preencherSelects(data);
        })
        .catch(() => {
            mostrarFeedback('Erro ao carregar formulário.', 'error');
        });
}

function fecharModalNovoAgente(e) {
    if (e && e.target !== document.getElementById('agModalOverlay')) return;
    document.getElementById('agModalOverlay').classList.remove('active');
}

function preencherSelects(data) {
    popularSelect('selectCarteira', data.carteiras, 'nome');
    popularSelect('selectEquipe',   data.equipes,   'nome');
    popularSelect('selectPerfil',   data.perfis,    'codigo');
}

function popularSelect(id, itens, labelKey) {
    const sel = document.getElementById(id);
    sel.innerHTML = '<option value="">Selecione...</option>';
    itens.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.id;
        opt.textContent = item[labelKey];
        sel.appendChild(opt);
    });
}

function limparModal() {
    document.getElementById('novoAgenteForm').reset();
    document.getElementById('agModalFeedback').className = 'ag-modal-feedback';
    document.getElementById('agModalFeedback').textContent = '';
    document.querySelectorAll('.ag-form-error').forEach(el => {
        el.textContent = '';
        el.classList.remove('visible');
    });
    document.querySelectorAll('.ag-form-input.error').forEach(el => {
        el.classList.remove('error');
    });
}

function mostrarFeedback(msg, tipo) {
    const el = document.getElementById('agModalFeedback');
    el.textContent = msg;
    el.className = `ag-modal-feedback ag-modal-feedback--${tipo}`;
}

function salvarNovoAgente() {
    const form = document.getElementById('novoAgenteForm');
    const btn  = document.getElementById('btnSalvarAgente');

    // Limpa erros
    document.querySelectorAll('.ag-form-error').forEach(el => {
        el.textContent = '';
        el.classList.remove('visible');
    });
    document.querySelectorAll('.ag-form-input.error').forEach(el => {
        el.classList.remove('error');
    });

    const data = Object.fromEntries(new FormData(form));

    btn.disabled = true;
    btn.textContent = 'Salvando...';

    fetch('/usuarios/novo_agente/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(async r => {
        const d = await r.json();
        if (!r.ok) throw d;
        return d;
    })
    .then(d => {
        mostrarFeedback('✓ Agente cadastrado com sucesso!', 'success');
        setTimeout(() => {
            fecharModalNovoAgente();
            location.reload();
        }, 1200);
    })
    .catch(err => {
        const msgs = err?.messages?.agente || {};
        let temErro = false;

        Object.entries(msgs).forEach(([campo, erros]) => {
            if (campo === '__all__' || campo === 'success') {
                mostrarFeedback(erros.join(' '), campo === 'success' ? 'success' : 'error');
                return;
            }
            const errEl  = document.getElementById(`err-${campo}`);
            const inpEl  = form.querySelector(`[name="${campo}"]`);
            if (errEl) {
                errEl.textContent = Array.isArray(erros) ? erros.join(' ') : erros;
                errEl.classList.add('visible');
            }
            if (inpEl) inpEl.classList.add('error');
            temErro = true;
        });

        if (!temErro && !Object.keys(msgs).length) {
            mostrarFeedback('Erro ao cadastrar agente. Tente novamente.', 'error');
        }
    })
    .finally(() => {
        btn.disabled = false;
        btn.textContent = 'Cadastrar Agente';
    });
}

// ── Toggle ativo/inativo ────────────────────────────────────
function toggleAgente(agenteId, btn) {
    const row = document.getElementById(`ag-row-${agenteId}`);

    fetch(`/usuarios/agente/${agenteId}/toggle/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(async r => {
        const d = await r.json();
        if (!r.ok) throw d;
        return d;
    })
    .then(d => {
        const statusEl = row.querySelector('.ag-status');
        if (d.is_active) {
            row.classList.remove('ag-row--inativo');
            statusEl.className = 'ag-status ag-status--ativo';
            statusEl.textContent = 'Ativo';
            btn.textContent = '🔒';
            btn.title = 'Desativar agente';
        } else {
            row.classList.add('ag-row--inativo');
            statusEl.className = 'ag-status ag-status--inativo';
            statusEl.textContent = 'Inativo';
            btn.textContent = '🔓';
            btn.title = 'Ativar agente';
        }
        // Atualiza contadores
        atualizarContadores();
    })
    .catch(() => alert('Erro ao alterar status do agente.'));
}

function atualizarContadores() {
    const total    = document.querySelectorAll('.ag-row').length;
    const inativos = document.querySelectorAll('.ag-row--inativo').length;
    const ativos   = total - inativos;

    document.querySelector('.ag-counter--total .ag-counter__num').textContent   = total;
    document.querySelector('.ag-counter--ativo .ag-counter__num').textContent   = ativos;
    document.querySelector('.ag-counter--inativo .ag-counter__num').textContent = inativos;
}

// Fecha modal com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') document.getElementById('agModalOverlay').classList.remove('active');
});