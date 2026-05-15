// bancos.js — Configurações de Referências › Bancos

let _bancoId = null;

const BK_URLS = {
    detail: (id) => id ? `/clientes/banco/${id}/` : '/clientes/banco/',
};

// ── Tabs ─────────────────────────────────────────────────────
function bkSetTab(tab) {
    document.querySelectorAll('.bk-tab').forEach(t =>
        t.classList.toggle('active', t.dataset.tab === tab)
    );
    document.querySelectorAll('.bk-panel').forEach(p =>
        p.classList.toggle('active', p.id === `panel-${tab}`)
    );
}

// ── Drawer ───────────────────────────────────────────────────
function bkAbrirDrawer(bancoId) {
    _bancoId = bancoId;
    _resetDrawer();

    document.getElementById('bkDrawerTitle').textContent    = bancoId ? 'Editar Banco' : 'Novo Banco';
    document.getElementById('bkDrawerSubtitle').textContent = bancoId ? 'Altere os dados do banco' : 'Preencha os dados abaixo';
    document.getElementById('bkBtnLabel').textContent       = bancoId ? 'Salvar' : 'Criar';

    document.getElementById('bkOverlay').classList.add('active');
    document.getElementById('bkDrawer').classList.add('active');

    fetch(BK_URLS.detail(bancoId))
        .then(r => r.json())
        .then(data => {
            document.getElementById('bkSpinner').style.display = 'none';
            document.getElementById('bkForm').style.display    = 'block';
            document.getElementById('bk_cod').value  = data.banco.cod_banco  || '';
            document.getElementById('bk_nome').value = data.banco.nome_banco || '';
        })
        .catch(() => _feedback('Erro ao carregar dados.', 'error'));
}

function bkFecharDrawer() {
    document.getElementById('bkOverlay').classList.remove('active');
    document.getElementById('bkDrawer').classList.remove('active');
    _bancoId = null;
}

// ── Salvar ────────────────────────────────────────────────────
function bkSalvar() {
    _limparErros();

    const cod  = document.getElementById('bk_cod').value.trim();
    const nome = document.getElementById('bk_nome').value.trim();

    let valido = true;
    if (!cod)  { _mostrarErro('err_cod_banco',  'bk_cod',  'Campo obrigatório.'); valido = false; }
    if (!nome) { _mostrarErro('err_nome_banco', 'bk_nome', 'Campo obrigatório.'); valido = false; }
    if (!valido) return;

    const btn = document.getElementById('bkBtnSalvar');
    btn.disabled = true;
    btn.innerHTML = '<span>Salvando…</span>';

    fetch(BK_URLS.detail(_bancoId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': _getCsrf() },
        body: JSON.stringify({ cod_banco: cod, nome_banco: nome }),
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) {
            _mostrarErrosServidor(data.messages?.banco || {});
            return;
        }
        _feedback(data.msg, 'success');
        _atualizarTabela(data.banco);
        setTimeout(bkFecharDrawer, 900);
    })
    .catch(() => _feedback('Erro de comunicação com o servidor.', 'error'))
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = `<span>${_bancoId ? 'Salvar' : 'Criar'}</span>`;
    });
}

// ── Atualizar tabela ──────────────────────────────────────────
function _atualizarTabela(banco) {
    document.getElementById('bk-row-empty')?.remove();

    let row = document.getElementById(`bk-row-${banco.id}`);
    if (!row) {
        row = document.createElement('tr');
        row.id = `bk-row-${banco.id}`;
        document.getElementById('bkTbody').prepend(row);

        const cnt = document.getElementById('bkCountBancos');
        if (cnt) cnt.textContent = parseInt(cnt.textContent || '0') + 1;
    }

    row.innerHTML = `
        <td><span class="bk-cod">${_esc(banco.cod_banco)}</span></td>
        <td class="bk-nome-cell">${_esc(banco.nome_banco)}</td>
        <td>
            <button class="bk-btn-icon bk-btn-icon--edit"
                    title="Editar"
                    onclick="bkAbrirDrawer(${banco.id})">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M9.5 2.5l2 2L4 12H2v-2L9.5 2.5z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
                </svg>
            </button>
        </td>`;
}

// ── Helpers ───────────────────────────────────────────────────
function _resetDrawer() {
    document.getElementById('bkSpinner').style.display  = 'flex';
    document.getElementById('bkForm').style.display     = 'none';
    document.getElementById('bkFeedback').style.display = 'none';
    _limparErros();
}

function _limparErros() {
    document.querySelectorAll('.bk-form__error').forEach(el => {
        el.textContent = ''; el.style.display = 'none';
    });
    document.querySelectorAll('.bk-form__input--error').forEach(el =>
        el.classList.remove('bk-form__input--error')
    );
}

function _mostrarErro(errId, inputId, msg) {
    const err = document.getElementById(errId);
    const inp = document.getElementById(inputId);
    if (err) { err.textContent = msg; err.style.display = 'block'; }
    if (inp) inp.classList.add('bk-form__input--error');
}

function _mostrarErrosServidor(erros) {
    const mapa = {
        cod_banco:  ['err_cod_banco',  'bk_cod'],
        nome_banco: ['err_nome_banco', 'bk_nome'],
    };
    Object.entries(erros).forEach(([campo, msgs]) => {
        const ids = mapa[campo];
        if (ids) _mostrarErro(ids[0], ids[1], Array.isArray(msgs) ? msgs[0] : msgs);
        else _feedback(Array.isArray(msgs) ? msgs[0] : msgs, 'error');
    });
}

function _feedback(msg, tipo) {
    const el = document.getElementById('bkFeedback');
    el.textContent = msg;
    el.className = `bk-feedback bk-feedback--${tipo}`;
    el.style.display = 'block';
}

function _getCsrf() {
    return document.cookie.split('; ')
        .find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

function _esc(str) {
    return String(str || '')
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') bkFecharDrawer();
});