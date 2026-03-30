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

    resultado.innerHTML = '<p class="receptivo-vazio">Buscando...</p>';

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
        resultado.innerHTML = `<p class="receptivo-vazio">${err.message || 'Nenhum cliente encontrado.'}</p>`;
    });
}

function renderResultado(clientes) {
    const resultado = document.getElementById('receptivoResultado');

    // se vier um id único (busca por CPF retorna id direto)
    if (typeof clientes === 'number') {
        window.location.href = `/clientes/atendimento/${clientes}`;
        return;
    }

    if (!clientes || clientes.length === 0) {
        resultado.innerHTML = '<p class="receptivo-vazio">Nenhum cliente encontrado.</p>';
        return;
    }

    resultado.innerHTML = clientes.map(c => `
        <div class="receptivo-resultado-item">
            <div class="receptivo-resultado-info">
                <span class="receptivo-resultado-nome">${c.nome}</span>
                <span class="receptivo-resultado-doc">${c.documento}</span>
            </div>
            <a href="/clientes/atendimento/${c.id}" class="btn-entrar" style="width:auto; padding: 6px 16px">
                Atender <span>→</span>
            </a>
        </div>
    `).join('');
}