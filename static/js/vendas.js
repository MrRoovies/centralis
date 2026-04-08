// venda.js
function initVendaForm(){
    const parceiro = document.getElementById("id_venda-parceiro");
    const produto = document.getElementById("id_venda-produto");
    const oferta = document.getElementById("id_venda-oferta");

    if(!parceiro || !produto || !oferta) return;

    /* Popular Parceiros */
    fetch(`/vendas/parceiros/`)
        .then(res => res.json())
        .then(data => popularSelect("id_venda-parceiro", data.parceiros));

    parceiro.addEventListener("change", function () {
        produto.innerHTML = '<option value="">Selecione...</option>';
        oferta.innerHTML = '<option value="">Selecione...</option>';
        buscarProdutos(this.value);
    });

    produto.addEventListener("change", function () {
        oferta.innerHTML = '<option value="">Selecione...</option>';
        buscarOfertas(parceiro.value, this.value);
    });
}

function buscarProdutos(parceiroId) {
    fetch(`/vendas/produtos/?parceiro_id=${parceiroId}`)
        .then(res => res.json())
        .then(data => popularSelect("id_venda-produto", data.produtos));
}

function buscarOfertas(parceiroId, produtoId) {
    fetch(`/vendas/ofertas/?parceiro_id=${parceiroId}&produto_id=${produtoId}`)
        .then(res => res.json())
        .then(data => popularSelect("id_venda-oferta", data.ofertas));
}

function popularSelect(elementId, itens) {
    const select = document.getElementById(elementId);
    select.innerHTML = '<option value="">Selecione...</option>';
    itens.forEach(item => {
        const option = document.createElement("option");
        option.value = item.id;
        option.text = item.nome;
        select.appendChild(option);
    });
}

function initVendaSubmit() {
    const vendaForm = document.querySelector("#vendaForm");
    vendaForm.addEventListener("submit", function (e){
        e.preventDefault();

        const formData = new FormData(vendaForm);

        fetch("/vendas/novo_contrato", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": vendaForm.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(async response => {
            const r = await response.json();
            if(!response.ok){ throw r; }
            return r;
        })
        .then( r => {
            // Junta erros de múltiplos forms em um único objeto
            const groupedMessages = r.messages;
            const allMessages = flattenGroupedMessages(groupedMessages);
            // Renderiza mensagens no formulário
            renderFormMessage(vendaForm, allMessages);
        })
        .catch( error => {
            // Caso erro de validação retornado via throw
            const groupedErrors = error.messages;
            let allErrors = flattenGroupedMessages(groupedErrors);
            renderFormMessage(vendaForm, allErrors);
        })
    })
}


/* Relatorio de Vendas */
function abrirDetalhe(id) {
    document.getElementById('vl-modal-overlay').classList.add('active');
    document.getElementById('vl-modal').classList.add('active');
    document.getElementById('vl-modal-body').innerHTML =
        '<div class="vl-spinner-wrap"><div class="vl-spinner"></div></div>';

    fetch(`/relatorios/detalhe/${id}/`)
        .then(r => r.json())
        .then(data => {
            const hist = data.historico.map(h => `
                <div class="vl-hist-item">
                    <div class="vl-hist-item__esteira">${h.esteira}</div>
                    <div class="vl-hist-item__meta">
                        <span>${h.usuario}</span>
                        <span>${h.data}</span>
                    </div>
                    ${h.comentario ? `<p class="vl-hist-item__coment">${h.comentario}</p>` : ''}
                </div>
            `).join('');

            document.getElementById('vl-modal-body').innerHTML = `
                <div class="vl-detalhe-info">
                    <div class="vl-detalhe-row">
                        <span>Contrato</span><strong>${data.contrato}</strong>
                    </div>
                    <div class="vl-detalhe-row">
                        <span>Cliente</span><strong>${data.cliente}</strong>
                    </div>
                    <div class="vl-detalhe-row">
                        <span>Produto</span><strong>${data.produto}</strong>
                    </div>
                    <div class="vl-detalhe-row">
                        <span>Parceiro</span><strong>${data.parceiro}</strong>
                    </div>
                    <div class="vl-detalhe-row">
                        <span>Valor</span><strong>R$ ${data.valor}</strong>
                    </div>
                </div>
                <h4 class="vl-hist-title">Movimentações</h4>
                <div class="vl-hist-list">${hist || '<p style="color:#aaa;font-size:13px">Sem histórico.</p>'}</div>
            `;
        })
        .catch(() => {
            document.getElementById('vl-modal-body').innerHTML =
                '<p style="color:#c33; text-align:center; padding:20px">Erro ao carregar detalhes.</p>';
        });
}

function fecharDetalhe() {
    document.getElementById('vl-modal-overlay').classList.remove('active');
    document.getElementById('vl-modal').classList.remove('active');
}