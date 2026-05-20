/* EVENTOS DE E-MAIL */

// Escuta qualquer clique no documento (event delegation)
// Isso evita precisar adicionar listener em cada botão individualmente
document.addEventListener('click', function(e){

    // Verifica se o clique foi em um elemento com classe .action-btn
    // ou em algum filho dele
    const btn = e.target.closest(".action-btn");
    if(!btn){ return; } // Se não for botão de ação, sai

    e.preventDefault();  // Evita comportamento padrão (ex: link)

    const action = btn.dataset.action;
    const type = btn.dataset.type;
    const id = btn.dataset.cliente;
    const target = btn.dataset.target;

    const delete_form = document.querySelector(`#form_del_${type}`);
    if (!delete_form){ return; }

    // Fluxo específico para ação de DELETE
    if (action === "delete") {
        // Faz requisição POST para endpoint dinâmico
        fetch(`/clientes/${type}/${id}/${action}`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken'),  // Token CSRF (Django)
                'Content-Type': 'application/json'},
        })
        .then(async response => {
            const data = await response.json();
            if(!response.ok){
                // Se a resposta for erro HTTP, lança o JSON como erro
                throw data;
            }
            return data;
        })
        .then( data => {
            // Junta erros de múltiplos forms em um único objeto
            const groupedMessages = data.messages;
            const allMessages = flattenGroupedMessages(groupedMessages);

            // Renderiza mensagens no formulário
            renderFormMessage(delete_form, allMessages);
        })
        .catch( error => {
            const groupedMessages = error.messages;
            const allMessages = flattenGroupedMessages(groupedMessages);

            // Renderiza mensagens no formulário
            renderFormMessage(delete_form, allMessages);
        })
    }
})

document.addEventListener("DOMContentLoaded", function() {
    const container = document.getElementById("historico-agendas");
    if (container) {
        const clienteId = container.dataset.clienteId;
        historico_agenda(clienteId);
    }
});

function historico_agenda(cliente_id){
    /* CARREGA OS DADOS DE AGENDA DO CLIENTE CASO EXISTA */
    fetch(`/agenda/historico/${cliente_id}/`)
        .then(response => response.text())
        .then(html => {
            document.getElementById("historico-agendas").innerHTML = html;
        })
        .catch(error => {
            document.getElementById("historico-agendas").innerHTML =
                "<p>Erro ao carregar histórico.</p>";
        });
}

// Toggle Dropdown
function dropdownhandler(headerId, bodyId){
    document.getElementById(headerId).classList.toggle('active');
    document.getElementById(bodyId).classList.toggle('active');
}

// ─── part-financeiro.html ────────────────────────────────────
// Acrescentar ao static/js/clientes.js

/**
 * Alterna entre os painéis Financeiro / Dívidas dentro de um vínculo.
 * @param {string} vinculoId  — id do Vinculo
 * @param {string} panel      — 'financeiro' | 'dividas'
 * @param {Element} tabEl     — elemento <button> clicado
 */
function cfinSetTab(vinculoId, panel, tabEl) {
    // Desativa todas as tabs do vínculo
    const tabsBar = document.getElementById(`cfin-tabs-${vinculoId}`);
    tabsBar.querySelectorAll('.cfin-tab').forEach(t => t.classList.remove('active'));

    // Oculta todos os painéis do vínculo
    ['financeiro', 'dividas'].forEach(p => {
        const el = document.getElementById(`cfin-${vinculoId}-${p}`);
        if (el) el.classList.remove('active');
    });

    // Ativa a tab e o painel selecionados
    tabEl.classList.add('active');
    const painelEl = document.getElementById(`cfin-${vinculoId}-${panel}`);
    if (painelEl) painelEl.classList.add('active');
}

/**
 * Alterna entre vínculos do mesmo cliente (quando há mais de um).
 * @param {string}  vinculoId — id do Vinculo
 * @param {Element} btnEl     — elemento <button> clicado
 */
function cfinSetVinculo(vinculoId, btnEl) {
    // Desativa todos os botões seletores
    btnEl.closest('.cfin-vinc-selector')
         .querySelectorAll('.cfin-vinc-btn')
         .forEach(b => b.classList.remove('active'));

    // Oculta todos os painéis de vínculo
    document.querySelectorAll('.cfin-vinc-panel')
            .forEach(p => p.classList.remove('active'));

    // Ativa o selecionado
    btnEl.classList.add('active');
    const painel = document.getElementById(`cfin-vinc-${vinculoId}`);
    if (painel) painel.classList.add('active');
}