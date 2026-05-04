// view_permissions.js — Gestão de Permissões por URL

// ── Estado ───────────────────────────────────────────────────
let _permId      = null;   // null = criação, number = edição
let _deleteId    = null;   // id aguardando confirmação de exclusão
let _rolesAtivas = new Set();

// ── Roles disponíveis (espelha role_choices do backend) ───────
// Os valores vêm renderizados na tabela; os atalhos usam essa lista.
const ROLES_GESTORES = ['ADM', 'DIRETOR', 'GERENTE', 'SUPERVISOR'];

// ════════════════════════════════════════════════════════════
// DRAWER — Abrir / Fechar
// ════════════════════════════════════════════════════════════

function abrirDrawer(permId) {
    _permId      = permId;
    _rolesAtivas = new Set();

    _resetDrawer();

    document.getElementById('vpDrawerTitle').textContent =
        permId ? 'Editar Permissão' : 'Nova Permissão';
    document.getElementById('vpDrawerSubtitle').textContent =
        permId ? 'Altere os campos desejados' : 'Defina quais perfis acessam esta URL';
    document.getElementById('vpBtnLabel').textContent =
        permId ? 'Salvar' : 'Criar';

    document.getElementById('vpOverlay').classList.add('active');
    document.getElementById('vpDrawer').classList.add('active');

    if (permId) {
        // Carregar dados existentes
        fetch(`/usuarios/permissoes/${permId}/`)
            .then(r => r.json())
            .then(data => _preencherForm(data))
            .catch(() => _mostrarFeedback('Erro ao carregar dados.', 'error'));
    } else {
        // Novo: exibe form vazio imediatamente
        document.getElementById('vpSpinner').style.display = 'none';
        document.getElementById('vpForm').style.display    = 'block';
    }
}

function fecharDrawer() {
    document.getElementById('vpOverlay').classList.remove('active');
    document.getElementById('vpDrawer').classList.remove('active');
    _permId = null;
}

// ════════════════════════════════════════════════════════════
// FORMULÁRIO — Preencher / Coletar
// ════════════════════════════════════════════════════════════

function _preencherForm(data) {
    const perm = data.permissao || {};

    document.getElementById('vp_url_name').value = perm.url_name || '';

    // Marcar roles existentes
    _rolesAtivas = new Set(perm.roles || []);
    _sincronizarRolesUI();

    document.getElementById('vpSpinner').style.display = 'none';
    document.getElementById('vpForm').style.display    = 'block';
}

// ════════════════════════════════════════════════════════════
// ROLES — Toggle e atalhos
// ════════════════════════════════════════════════════════════

function toggleRole(el) {
    const role = el.dataset.role;

    if (_rolesAtivas.has(role)) {
        _rolesAtivas.delete(role);
        el.classList.remove('selected');
    } else {
        _rolesAtivas.add(role);
        el.classList.add('selected');
    }

    _atualizarResumo();
    _limparErro('err-roles');
}

function selecionarTodos() {
    document.querySelectorAll('.vp-role-option').forEach(el => {
        _rolesAtivas.add(el.dataset.role);
    });
    _sincronizarRolesUI();
}

function limparSelecao() {
    _rolesAtivas.clear();
    _sincronizarRolesUI();
}

function selecionarGestores() {
    _rolesAtivas = new Set(ROLES_GESTORES);
    _sincronizarRolesUI();
}

function _sincronizarRolesUI() {
    document.querySelectorAll('.vp-role-option').forEach(el => {
        const ativo = _rolesAtivas.has(el.dataset.role);
        el.classList.toggle('selected', ativo);
    });
    _atualizarResumo();
}

function _atualizarResumo() {
    const container = document.getElementById('vpRolesSummary');

    if (_rolesAtivas.size === 0) {
        container.innerHTML =
            '<span class="vp-roles-summary__empty">Nenhum perfil selecionado — acesso bloqueado</span>';
        return;
    }

    const badgesHtml = [..._rolesAtivas].map(r =>
        `<span class="vp-role-badge vp-role-badge--${r}">${r}</span>`
    ).join('');

    container.innerHTML = badgesHtml;
}

// ════════════════════════════════════════════════════════════
// SALVAR
// ════════════════════════════════════════════════════════════

function salvarPermissao() {
    _limparErros();

    const urlName = document.getElementById('vp_url_name').value.trim();
    const roles   = [..._rolesAtivas];

    // Validação básica no front
    let valido = true;

    if (!urlName) {
        _mostrarErro('err-url-name', 'O nome da URL é obrigatório.');
        document.getElementById('vp_url_name').classList.add('vp-form__input--error');
        valido = false;
    }

    if (!valido) return;

    const btn   = document.getElementById('vpBtnSalvar');
    const label = document.getElementById('vpBtnLabel');
    btn.disabled      = true;
    label.textContent = 'Salvando...';

    const url    = _permId
        ? `/usuarios/permissoes/${_permId}/`
        : '/usuarios/permissoes/nova/';

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url_name: urlName, roles }),
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const msg = d.messages?.permissao?.success?.[0] || '✓ Permissão salva com sucesso!';
        _mostrarFeedback(msg, 'success');
        setTimeout(() => { fecharDrawer(); location.reload(); }, 900);
    })
    .catch(err => {
        const msgs = err?.messages?.permissao || {};

        Object.entries(msgs).forEach(([campo, erros]) => {
            const txt = Array.isArray(erros) ? erros.join(' ') : erros;

            if (campo === '__all__') {
                _mostrarFeedback(txt, 'error');
                return;
            }

            const errId = campo === 'url_name' ? 'err-url-name'
                        : campo === 'roles'    ? 'err-roles'
                        : null;

            if (errId) _mostrarErro(errId, txt);

            if (campo === 'url_name') {
                document.getElementById('vp_url_name').classList.add('vp-form__input--error');
            }
        });

        if (!Object.keys(msgs).length) {
            _mostrarFeedback('Erro ao salvar. Tente novamente.', 'error');
        }
    })
    .finally(() => {
        btn.disabled      = false;
        label.textContent = _permId ? 'Salvar' : 'Criar';
    });
}

// ════════════════════════════════════════════════════════════
// EXCLUSÃO
// ════════════════════════════════════════════════════════════

function confirmarExclusao(permId, urlName) {
    _deleteId = permId;
    document.getElementById('vpConfirmUrl').textContent = urlName;
    document.getElementById('vpConfirmOverlay').classList.add('active');
}

function fecharConfirm() {
    _deleteId = null;
    document.getElementById('vpConfirmOverlay').classList.remove('active');
}

function executarExclusao() {
    if (!_deleteId) return;

    const btn = document.getElementById('vpBtnConfirmDelete');
    btn.disabled    = true;
    btn.textContent = 'Excluindo...';

    fetch(`/usuarios/permissoes/${_deleteId}/excluir/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(() => {
        // Remove a linha da tabela sem reload
        const row = document.getElementById(`vp-row-${_deleteId}`);
        if (row) {
            row.style.transition = 'opacity .3s, transform .3s';
            row.style.opacity    = '0';
            row.style.transform  = 'translateX(20px)';
            setTimeout(() => {
                row.remove();
                _atualizarContadores();
            }, 300);
        }
        fecharConfirm();
    })
    .catch(() => {
        btn.disabled    = false;
        btn.textContent = 'Sim, excluir';
        alert('Erro ao excluir. Tente novamente.');
    });
}

// ════════════════════════════════════════════════════════════
// FILTRO DA TABELA
// ════════════════════════════════════════════════════════════

function filtrarTabela() {
    const termoBusca = document.getElementById('filtroUrl').value.toLowerCase().trim();
    const roleFilter = document.getElementById('filtroRole').value;
    const appFilter = document.getElementById('filtroApp').value;

    const rows = document.querySelectorAll('#vpTableBody .vp-row');
    let visiveis = 0;

    rows.forEach(row => {
        const url   = (row.dataset.url   || '').toLowerCase();
        const roles = (row.dataset.roles || '');
        const apps = (row.dataset.apps || '');

        const passaBusca = !termoBusca || url.includes(termoBusca);
        const passaRole  = !roleFilter || roles.split(',').includes(roleFilter);
        const passaApp  = !appFilter || apps.includes(appFilter);

        const visivel = passaBusca && passaRole && passaApp;

        row.style.display = visivel ? '' : 'none';
        if (visivel) visiveis++;
    });

    // Mostra empty state se nenhuma linha visível
    _toggleEmpty(visiveis === 0);
}

function _toggleEmpty(mostrar) {
    let emptyEl = document.getElementById('vpEmptyFiltro');

    if (mostrar && !emptyEl) {
        const wrap = document.querySelector('.vp-table-wrap');
        emptyEl = document.createElement('div');
        emptyEl.id = 'vpEmptyFiltro';
        emptyEl.className = 'vp-empty';
        emptyEl.innerHTML = `
            <div class="vp-empty__icon">🔍</div>
            <p class="vp-empty__title">Nenhum resultado encontrado</p>
            <p class="vp-empty__sub">Tente ajustar os filtros acima.</p>`;
        wrap.appendChild(emptyEl);
    } else if (!mostrar && emptyEl) {
        emptyEl.remove();
    }
}

// ════════════════════════════════════════════════════════════
// CONTADORES (atualiza após exclusão)
// ════════════════════════════════════════════════════════════

function _atualizarContadores() {
    const rows     = document.querySelectorAll('#vpTableBody .vp-row');
    let publico    = 0;
    let restrito   = 0;

    rows.forEach(row => {
        const roles = (row.dataset.roles || '').trim();
        if (roles.length === 0) publico++;
        else restrito++;
    });

    const el = (id) => document.getElementById(id);
    if (el('cntTotal'))    el('cntTotal').textContent    = rows.length;
    if (el('cntPublico'))  el('cntPublico').textContent  = publico;
    if (el('cntRestrito')) el('cntRestrito').textContent = restrito;
}

// ════════════════════════════════════════════════════════════
// HELPERS
// ════════════════════════════════════════════════════════════

function _resetDrawer() {
    document.getElementById('vpSpinner').style.display = 'flex';
    document.getElementById('vpForm').style.display    = 'none';
    document.getElementById('vpFeedback').style.display = 'none';
    document.getElementById('vp_url_name').value = '';
    _rolesAtivas = new Set();
    _sincronizarRolesUI();
    _limparErros();
}

function _limparErros() {
    ['err-url-name', 'err-roles'].forEach(id => _limparErro(id));
    document.getElementById('vp_url_name').classList.remove('vp-form__input--error');
}

function _limparErro(id) {
    const el = document.getElementById(id);
    if (el) { el.textContent = ''; el.style.display = 'none'; }
}

function _mostrarErro(id, msg) {
    const el = document.getElementById(id);
    if (el) { el.textContent = msg; el.style.display = 'block'; }
}

function _mostrarFeedback(msg, tipo) {
    const el = document.getElementById('vpFeedback');
    el.textContent = msg;
    el.className = `vp-drawer__feedback vp-drawer__feedback--${tipo}`;
    el.style.display = 'block';

    if (tipo === 'success') {
        setTimeout(() => { el.style.display = 'none'; }, 3000);
    }
}

// ── Fecha com ESC ─────────────────────────────────────────────
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        fecharConfirm();
        fecharDrawer();
    }
});