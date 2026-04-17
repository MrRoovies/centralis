let _agenteIdAtual = null;

// ── Abrir drawer ────────────────────────────────────────────
function abrirDrawerEditar(agenteId, nomeAgente) {
    _agenteIdAtual = agenteId;

    // Inicializa UI
    document.getElementById('agDrawerOverlay').classList.add('active');
    document.getElementById('agDrawer').classList.add('active');
    document.getElementById('drawerNomeAgente').textContent = nomeAgente;

    // Avatar (iniciais)
    const partes = nomeAgente.trim().split(' ');
    const iniciais = partes.length >= 2
        ? partes[0][0] + partes[partes.length - 1][0]
        : nomeAgente.slice(0, 2);
    document.getElementById('drawerAvatar').textContent = iniciais.toUpperCase();

    // Reset visual
    _limparDrawer();

    // Carrega dados do agente
    fetch(`/usuarios/agente/${agenteId}/editar/`)
        .then(r => r.json())
        .then(data => {
            _preencherFormulario(data);
        })
        .catch((err) => {
            const groupedErrors = err.messages;
            let allErrors = flattenGroupedMessages(groupedErrors);
            renderFormMessage(form, allErrors);

            triggerShake(form.id);
        });
}

// ── Fechar drawer ───────────────────────────────────────────
function fecharDrawerEditar() {
    document.getElementById('agDrawerOverlay').classList.remove('active');
    document.getElementById('agDrawer').classList.remove('active');
    _agenteIdAtual = null;
}

// ── Preencher formulário com dados recebidos ────────────────
function _preencherFormulario(data) {
    const { agente, perfis, equipes } = data;

    // Campos simples
    document.getElementById('edit_first_name').value = agente.first_name || '';
    document.getElementById('edit_last_name').value  = agente.last_name  || '';
    document.getElementById('edit_email').value      = agente.email      || '';
    document.getElementById('edit_cpf').value        = agente.cpf        || '';
    document.getElementById('edit_senha').value      = '';

    // Select de Perfis
    const selPerfil = document.getElementById('edit_perfil_id');
    selPerfil.innerHTML = '<option value="">Selecione...</option>';
    perfis.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.codigo;
        if (p.id === agente.perfil_id) opt.selected = true;
        selPerfil.appendChild(opt);
    });

    // Select de Equipes
    const selEquipe = document.getElementById('edit_equipe_id');
    selEquipe.innerHTML = '<option value="">Selecione...</option>';
    equipes.forEach(e => {
        const opt = document.createElement('option');
        opt.value = e.id;
        opt.textContent = e.nome;
        if (e.id === agente.equipe_id) opt.selected = true;
        selEquipe.appendChild(opt);
    });

    // Exibe formulário, oculta spinner
    document.getElementById('drawerSpinner').style.display = 'none';
    document.getElementById('editarAgenteForm').style.display = 'block';
}

// ── Salvar edição ───────────────────────────────────────────
function salvarEdicaoAgente() {
    if (!_agenteIdAtual) return;

    const form = document.getElementById('editarAgenteForm');
    const btn  = document.getElementById('btnSalvarEdicao');

    // Limpa erros anteriores
    _limparErros();

    const data = {
        first_name: document.getElementById('edit_first_name').value.trim(),
        last_name:  document.getElementById('edit_last_name').value.trim(),
        email:      document.getElementById('edit_email').value.trim(),
        cpf:        document.getElementById('edit_cpf').value.trim(),
        perfil_id:  document.getElementById('edit_perfil_id').value,
        equipe_id:  document.getElementById('edit_equipe_id').value,
        senha:      document.getElementById('edit_senha').value,
    };

    btn.disabled = true;
    btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"
             style="animation: ag-spin 0.7s linear infinite">
            <circle cx="7" cy="7" r="5" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
            <path d="M7 2a5 5 0 0 1 5 5" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>
        Salvando...`;

    fetch(`/usuarios/agente/${_agenteIdAtual}/editar/`, {
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
        const groupedMessages = d.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);
        renderFormMessage(form, allMessages);

        setTimeout(() => {
            fecharDrawerEditar();
            location.reload();
        }, 1000);
    })
    .catch(err => {
        const groupedErrors = err.messages;
        let allErrors = flattenGroupedMessages(groupedErrors);
        renderFormMessage(form, allErrors);

        triggerShake(form.id);
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 7l4 4 6-6" stroke="currentColor" stroke-width="2"
                      stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Salvar Alterações`;
    });
}

// ── Toggle visibilidade senha ───────────────────────────────
function toggleSenhaVisibility() {
    const input = document.getElementById('edit_senha');
    const isPass = input.type === 'password';
    input.type = isPass ? 'text' : 'password';

    // Troca ícone
    document.getElementById('iconOlho').innerHTML = isPass
        ? `<ellipse cx="8" cy="8" rx="6" ry="4" stroke="currentColor" stroke-width="1.5"/>
           <line x1="4" y1="4" x2="12" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>`
        : `<ellipse cx="8" cy="8" rx="6" ry="4" stroke="currentColor" stroke-width="1.5"/>
           <circle cx="8" cy="8" r="2" fill="currentColor"/>`;
}

// ── Helpers internos ────────────────────────────────────────
function _limparDrawer() {
    document.getElementById('drawerSpinner').style.display = 'flex';
    document.getElementById('editarAgenteForm').style.display = 'none';
    document.getElementById('drawerFeedback').style.display = 'none';
    _limparErros();
}

function _limparErros() {
    document.querySelectorAll('.ag-drawer__error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
    document.querySelectorAll('.ag-drawer__input--error').forEach(el => {
        el.classList.remove('ag-drawer__input--error');
    });
}

// Fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharDrawerEditar();
});