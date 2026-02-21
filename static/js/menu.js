// main.js - Lógica principal do sistema
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.querySelector(".search-icon").addEventListener('click', function(){
    const documento = document.getElementById("searchCliente").value;

    if (documento.trim() == ''){ alert("Digite um CPF ou CNPJ"); return; }

    fetch("/clientes/search_cliente", {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        body: JSON.stringify({'documento': documento })
    })
    .then( async response => {
        const data = await response.json();
        if( !response.ok ){ throw data; }
        return data;
    })
    .then( data => {
        console.log(data.data);
    })
    .catch( error => {
        alert( error.message );
    })
})

// Controle do menu lateral
function initMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (menuToggle && sidebar && sidebarOverlay) {
        // Toggle do menu
        menuToggle.addEventListener('click', function() {
            const isActive = sidebar.classList.contains('active');
            
            if (isActive) {
                // Fechar menu
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                menuToggle.classList.remove('active');
            } else {
                // Abrir menu
                sidebar.classList.add('active');
                sidebarOverlay.classList.add('active');
                menuToggle.classList.add('active');
            }
        });
        
        // Fechar ao clicar no overlay
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            menuToggle.classList.remove('active');
        });
        
        // Fechar ao clicar em um link do menu
        const menuLinks = sidebar.querySelectorAll('.sidebar-menu a');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                sidebar.classList.remove('active');
                sidebarOverlay.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });
    }
}

// Marca o menu ativo
function setActiveMenu() {
    const currentPage = window.location.pathname.split('/').pop();
    const menuLinks = document.querySelectorAll('.sidebar-menu a');
    
    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.includes(currentPage)) {
            link.classList.add('active');
        }
    });
}

// Inicializa quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    initMenu();
    setActiveMenu();
});

document.querySelector('.logout-btn').addEventListener('click', function(){
    fetch("/logout", {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.href = "/";
        }
    });
})

