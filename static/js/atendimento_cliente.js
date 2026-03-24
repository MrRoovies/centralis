// atendimento_campanha.js
// Gerencia o ciclo de vida do atendimento: iniciar, pausar, parar

const Estado = {
    PARADO:  'parado',
    RODANDO: 'rodando',
    PAUSADO: 'pausado',
};

let estadoAtual = Estado.PARADO;
let contAtendidos = 0;

// ─── Referências ao DOM ────────────────────────────────────────
const btnIniciar   = document.getElementById('btnIniciar');
const btnPausar    = document.getElementById('btnPausar');
const btnParar     = document.getElementById('btnParar');
const filaStatus   = document.getElementById('filaStatus');
const statusLabel  = document.getElementById('statusLabel');
const clienteArea  = document.getElementById('clienteArea');
const clienteInjetado = document.getElementById('clienteInjetado');
const contAtendidosEl = document.getElementById('contAtendidos');
const contRestantesEl = document.getElementById('contRestantes');

// ─── Controle de estado dos botões ────────────────────────────
function aplicarEstado(estado) {
    estadoAtual = estado;

    const configs = {
        [Estado.PARADO]: {
            label: 'Parado',
            classe: '',
            iniciar: false, pausar: true, parar: true,
        },
        [Estado.RODANDO]: {
            label: 'Rodando',
            classe: 'status-rodando',
            iniciar: true, pausar: false, parar: false,
        },
        [Estado.PAUSADO]: {
            label: 'Pausado',
            classe: 'status-pausado',
            iniciar: false, pausar: true, parar: false,
        },
    };

    const cfg = configs[estado];

    filaStatus.className = 'fila-status ' + cfg.classe;
    statusLabel.textContent = cfg.label;

    btnIniciar.disabled = cfg.iniciar;
    btnPausar.disabled  = cfg.pausar;
    btnParar.disabled   = cfg.parar;
}

// Executa caso exista cliente pendente de tabulação
document.addEventListener("DOMContentLoaded", function () {
    if (window.APP.temCliente) {
        iniciarFila(window.APP.campanhaId);
    }
});

// ─── Ações dos botões ─────────────────────────────────────────
function iniciarFila(id_campanha) {
    aplicarEstado(Estado.RODANDO);
    buscarProximoCliente(id_campanha);
}

function pausarFila() {
    aplicarEstado(Estado.PAUSADO);
    // Permite finalizar o cliente atual; não busca próximo
}

function pararFila() {
    aplicarEstado(Estado.PARADO);
    limparClienteArea();
}

// ─── Buscar próximo cliente da fila ───────────────────────────
function buscarProximoCliente(id_campanha) {
    if (estadoAtual !== Estado.RODANDO) return;

    mostrarLoading();

    fetch(`/campanhas/proximo_cliente/${id_campanha}/`, {
        method: 'GET',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) throw data;
        return data;
    })
    .then(data => {
        if (data.fim_da_fila) {
            aplicarEstado(Estado.PARADO);
            mostrarFimDeFila();
            atualizarContRestantes(0);
            return;
        }
        injetarCliente(data.html, data.restantes);
    })
    .catch(err => {
        console.error('Erro ao buscar cliente:', err);
        mostrarErro(err.message || 'Erro ao buscar próximo cliente.');
    });
}

// ─── Injetar HTML do cliente ───────────────────────────────────
function injetarCliente(html, restantes) {
    clienteArea.classList.add('com-cliente');
    clienteInjetado.innerHTML = html;
    atualizarContRestantes(restantes);

    // Recarrega o histórico de agendas (mesmo comportamento de clientes.js)
    const historicoEl = clienteInjetado.querySelector('#historico-agendas');
    if (historicoEl) {
        carrega_agenda(historicoEl.dataset.clienteId);
    }
}

// ─── Chamada externa: cliente finalizado → avança a fila ──────
// Deve ser chamada pelo código do card de cliente após salvar atendimento
function proximoCliente(campanhaId) {
    contAtendidos++;
    contAtendidosEl.textContent = contAtendidos;
    clienteArea.classList.remove('com-cliente');
    clienteInjetado.innerHTML = '';

    if (estadoAtual === Estado.RODANDO) {
        buscarProximoCliente(campanhaId);
    }
}

// ─── Helpers de UI ────────────────────────────────────────────
function mostrarLoading() {
    clienteArea.classList.remove('com-cliente');
    clienteInjetado.innerHTML = `
        <div class="cliente-loading">
            <div class="spinner"></div>
            <span>Buscando próximo cliente...</span>
        </div>`;
}

function mostrarFimDeFila() {
    clienteInjetado.innerHTML = `
        <div class="cliente-placeholder">
            <div class="placeholder-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <path d="M10 24L20 34L38 14" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <p class="placeholder-titulo">Fila concluída</p>
            <p class="placeholder-sub">Todos os clientes desta campanha foram atendidos.</p>
        </div>`;
    clienteArea.classList.add('com-cliente');
}

function mostrarErro(msg) {
    clienteInjetado.innerHTML = `
        <div class="cliente-placeholder">
            <p class="placeholder-titulo" style="color:#c33">Erro ao carregar cliente</p>
            <p class="placeholder-sub">${msg}</p>
            <button class="btn btn-primary" style="margin-top:16px" onclick="buscarProximoCliente()">Tentar novamente</button>
        </div>`;
    clienteArea.classList.add('com-cliente');
}

function limparClienteArea() {
    clienteArea.classList.remove('com-cliente');
    clienteInjetado.innerHTML = '';
}

function atualizarContRestantes(val) {
    contRestantesEl.textContent = val != null ? val : '—';
}

// ─── Inicialização ─────────────────────────────────────────────
aplicarEstado(Estado.PARADO);