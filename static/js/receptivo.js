// ---------------- Atendimento Receptivo ---------------------------

// Elementos centralizados
const el = {
    input: document.getElementById('receptivoInput'),
    resultado: document.getElementById('receptivoResultado'),
    btnBuscar: document.getElementById('btnBuscarReceptivo'),
    tabs: document.querySelectorAll('.receptivo-tab')
};

// Estado
const state = {
    campoBusca: 'documento'
};

// Configs
const PLACEHOLDERS = {
    documento: 'Digite o CPF do cliente...',
    nome: 'Digite o nome do cliente...',
    telefone: 'Digite o telefone do cliente...',
    email: 'Digite o e-mail do cliente...'
};

const CANAIS = [
    { id: 'WHATSAPP', label: 'WhatsApp', icon: '💬' },
    { id: 'CHAT',     label: 'Chat',     icon: '🖥️' },
    { id: 'EMAIL',    label: 'E-mail',   icon: '✉️' },
    { id: 'TELEFONE', label: 'Telefone', icon: '📞' },
];

// ---------------- Eventos ---------------------------

// Tabs
el.tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        el.tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        state.campoBusca = tab.dataset.field;

        updateInput();
        clearResultado();
    });
});

// Botão buscar
el.btnBuscar.addEventListener('click', buscarReceptivo);

// Enter no input
el.input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') buscarReceptivo();
});

// Event delegation (substitui TODOS os onclick)
el.resultado.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;

    if (action === 'selecionar') {
        renderCanais(btn.dataset.id, btn.dataset.nome);
    }

    if (action === 'canal') {
        iniciarAtendimentoReceptivo(btn.dataset.id, btn.dataset.canal);
    }

    if (action === 'voltar') {
        clearResultado();
    }
});

// ---------------- Funções ---------------------------

function updateInput() {
    el.input.value = '';
    el.input.placeholder = PLACEHOLDERS[state.campoBusca];
}

function clearResultado() {
    el.resultado.innerHTML = '';
}

// Fetch (async/await)
async function buscarReceptivo() {
    const valor = el.input.value.trim();
    if (!valor) return;

    try {
        const res = await fetch('/clientes/search_cliente', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ [state.campoBusca]: valor, 'modo': 'search' })
        });

        const data = await res.json();
        if (!res.ok) throw data;

        renderResultado(data.data);

    } catch (err) {
        SystemModal.showMessage(err.messages);
    }
}

// Render clientes
function renderResultado(clientes) {
    el.resultado.innerHTML = clientes.map(c => `
        <div class="receptivo-resultado-item">
            <div class="receptivo-resultado-info">
                <span class="receptivo-resultado-nome">${escapeHTML(c.nome)}</span>
                <span class="receptivo-resultado-doc">${escapeHTML(c.documento)}</span>
            </div>
            <button
                class="btn-receptivo-selecionar"
                data-action="selecionar"
                data-id="${c.id}"
                data-nome="${escapeHTML(c.nome)}">
                Selecionar →
            </button>
        </div>
    `).join('');
}

// Render canais
function renderCanais(clienteId, clienteNome) {
    const nomeLabel = clienteNome
        ? `<span class="canais-cliente-nome">${escapeHTML(clienteNome)}</span>`
        : '';

    el.resultado.innerHTML = `
        <div class="canais-box">
            <div class="canais-header">
                <span class="canais-titulo">Como o cliente está entrando em contato?</span>
                ${nomeLabel}
            </div>

            <div class="canais-grid">
                ${CANAIS.map(canal => `
                    <button
                        class="canal-btn"
                        data-action="canal"
                        data-id="${clienteId}"
                        data-canal="${canal.id}">
                        <span class="canal-icon">${canal.icon}</span>
                        <span class="canal-label">${canal.label}</span>
                    </button>
                `).join('')}
            </div>

            <button class="btn-canais-voltar" data-action="voltar">
                ← Voltar
            </button>
        </div>
    `;
}

// Segurança básica contra XSS
function escapeHTML(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function iniciarAtendimentoReceptivo(dataset_id, dataset_canal){
    console.log(dataset_id);
    console.log(dataset_canal);
}