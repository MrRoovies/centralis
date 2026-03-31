//---------------- Atendimento Receptivo ---------------------------
// receptivo.js
let campoBusca = 'documento';

// Troca de tab
document.querySelectorAll('.receptivo-tab').forEach(tab => {
    tab.addEventListener('click', function () {
        document.querySelectorAll('.receptivo-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');

        campoBusca = this.dataset.field;

        const placeholders = {
            documento: 'Digite o CPF do cliente...',
            nome:      'Digite o nome do cliente...',
            telefone:  'Digite o telefone do cliente...',
            email:     'Digite o e-mail do cliente...',
        };

        document.getElementById('receptivoInput').value = '';
        document.getElementById('receptivoInput').placeholder = placeholders[campoBusca];
        document.getElementById('receptivoResultado').innerHTML = '';
    });
});

// Busca ao clicar
document.getElementById('btnBuscarReceptivo').addEventListener('click', buscarReceptivo);

// Busca ao pressionar Enter
document.getElementById('receptivoInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') buscarReceptivo();
});

function buscarReceptivo() {
    const valor = document.getElementById('receptivoInput').value.trim();
    const resultado = document.getElementById('receptivoResultado');

    if (!valor) return;

    fetch('/clientes/search_cliente', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ [campoBusca]: valor })
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    })
    .then(data => {
        renderResultado(data.data);
    })
    .catch(err => {
        // Junta erros de múltiplos forms em um único objeto
        const groupedMessages = err.messages;
        // Renderiza mensagens no template
        SystemModal.showMessage(groupedMessages);
    });
}

function renderResultado(clientes) {
    const resultado = document.getElementById('receptivoResultado');

    // lista de clientes encontrados
    resultado.innerHTML = clientes.map(c => `
        <div class="receptivo-resultado-item">
            <div class="receptivo-resultado-info">
                <span class="receptivo-resultado-nome">${c.nome}</span>
                <span class="receptivo-resultado-doc">${c.documento}</span>
            </div>
            <button class="btn-receptivo-selecionar" onclick="renderCanais(${c.id}, '${c.nome}')">
                Selecionar <span>→</span>
            </button>
        </div>
    `).join('');

}

const CANAIS = [
    { id: 'WHATSAPP', label: 'WhatsApp', icon: '💬' },
    { id: 'CHAT',     label: 'Chat',     icon: '🖥️' },
    { id: 'EMAIL',    label: 'E-mail',   icon: '✉️' },
    { id: 'TELEFONE', label: 'Telefone', icon: '📞' },
];

function renderCanais(clienteId, clienteNome) {
    const resultado = document.getElementById('receptivoResultado');
    const nomeLabel = clienteNome
        ? `<span class="canais-cliente-nome">${clienteNome}</span>`
        : '';

    resultado.innerHTML = `
        <div class="canais-box">
            <div class="canais-header">
                <span class="canais-titulo">Como o cliente está entrando em contato?</span>
                ${nomeLabel}
            </div>
            <div class="canais-grid">
                ${CANAIS.map(canal => `
                    <button class="canal-btn" onclick="iniciarAtendimentoReceptivo(${clienteId}, '${canal.id}')">
                        <span class="canal-icon">${canal.icon}</span>
                        <span class="canal-label">${canal.label}</span>
                    </button>
                `).join('')}
            </div>
            <button class="btn-canais-voltar" onclick="document.getElementById('receptivoResultado').innerHTML = ''">
                ← Voltar
            </button>
        </div>
    `;
}