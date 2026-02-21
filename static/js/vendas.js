// vendas.js - Lógica do painel de vendas

// Dados simulados de vendas
let vendas = {
    dia: 15847.50,
    total: 37,
    ticket: 428.31,
    novos: 5
};

// Atualiza as informações de vendas na tela
function updateVendas() {
    const vendasDia = document.getElementById('vendasDia');
    const totalVendas = document.getElementById('totalVendas');
    const ticketMedio = document.getElementById('ticketMedio');
    const novosClientes = document.getElementById('novosClientes');
    
    if (vendasDia) {
        vendasDia.textContent = `R$ ${vendas.dia.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    }
    
    if (totalVendas) {
        totalVendas.textContent = vendas.total;
    }
    
    if (ticketMedio) {
        ticketMedio.textContent = `R$ ${vendas.ticket.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    }
    
    if (novosClientes) {
        novosClientes.textContent = vendas.novos;
    }
}

// Incrementa novos clientes (será chamado quando cadastrar um cliente)
function incrementarNovosClientes() {
    vendas.novos++;
    updateVendas();
    
    // Salva no localStorage para persistir
    localStorage.setItem('vendas', JSON.stringify(vendas));
}

// Carrega dados salvos
function loadVendas() {
    const vendasSalvas = localStorage.getItem('vendas');
    if (vendasSalvas) {
        vendas = JSON.parse(vendasSalvas);
    }
}

// Inicializa quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    loadVendas();
    updateVendas();
});
