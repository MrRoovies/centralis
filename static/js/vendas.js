// venda.js
alert("Ta nao ta");
document.addEventListener("DOMContentLoaded", function () {
    const parceiro = document.getElementById("id_venda-parceiro");
    const produto = document.getElementById("id_venda-produto");
    const oferta = document.getElementById("id_venda-oferta");

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