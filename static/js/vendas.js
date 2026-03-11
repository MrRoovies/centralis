// venda.js
document.addEventListener("DOMContentLoaded", function () {
    const parceiro = document.getElementById("id_venda-parceiro");
    const produto = document.getElementById("id_venda-produto");
    const oferta = document.getElementById("id_venda-oferta");

    /* Popular Parceiros */
    fetch(`/vendas/parceiros/`)
        .then(res => res.json())
        .then(data => popularSelect("id_venda-parceiro", data.parceiros));

    parceiro.addEventListener("change", function () {
        buscarProdutos(this.value);
    });

    produto.addEventListener("change", function () {
        buscarOfertas(parceiro.value, this.value);
    });
});

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
        const groupedErrors = error.errors;
        let allErrors = flattenGroupedMessages(groupedErrors);
        renderFormMessage(vendaForm, allErrors);
    })
})