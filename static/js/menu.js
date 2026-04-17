/* ============================================================
   menu.js — sidebar com grupos em cascata
   ============================================================ */

// ── Pesquisa de cliente na barra do header ───────────────────
document.querySelector('.search-icon').addEventListener('click', function () {
    const documento = document.getElementById('searchCliente').value;
    if (documento.trim() === '') { alert('Digite um CPF ou CNPJ'); return; }

    fetch('/clientes/search_cliente', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ documento, modo: 'lookup' })
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) throw data;
        return data;
    })
    .then(data => { window.location.href = `/clientes/cliente/${data.id}`; })
    .catch(error => {
        alert(error.message);
        window.location.href = '/clientes/cliente_novo';
    });
});

// ── Toggle sidebar (hambúrguer) ──────────────────────────────
function initMenu() {
    const menuToggle    = document.getElementById('menuToggle');
    const sidebar       = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    if (!menuToggle || !sidebar || !sidebarOverlay) return;

    menuToggle.addEventListener('click', () => {
        const isActive = sidebar.classList.contains('active');
        sidebar.classList.toggle('active', !isActive);
        sidebarOverlay.classList.toggle('active', !isActive);
        menuToggle.classList.toggle('active', !isActive);
    });

    sidebarOverlay.addEventListener('click', closeSidebar);

    // Links simples (não-grupo) fecham o sidebar no mobile
    document.querySelectorAll('.menu-link').forEach(link => {
        link.addEventListener('click', closeSidebar);
    });
}

function closeSidebar() {
    document.getElementById('sidebar')?.classList.remove('active');
    document.getElementById('sidebarOverlay')?.classList.remove('active');
    document.getElementById('menuToggle')?.classList.remove('active');
}

// ── Cascata de grupos ────────────────────────────────────────
const STORAGE_KEY = 'sidebar_open_groups';

function getSavedGroups() {
    try { return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || []; }
    catch { return []; }
}

function saveGroups(list) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function toggleGroup(groupId) {
    const submenu = document.getElementById(`submenu-${groupId}`);
    const trigger = document.querySelector(`#group-${groupId} .menu-group-trigger`);
    if (!submenu) return;

    const isOpen = submenu.classList.contains('open');

    // Fecha todos os outros grupos
    document.querySelectorAll('.menu-submenu.open').forEach(el => {
        if (el.id !== `submenu-${groupId}`) {
            el.classList.remove('open');
            el.style.maxHeight = '0';
            const otherId  = el.id.replace('submenu-', '');
            const otherTrigger = document.querySelector(`#group-${otherId} .menu-group-trigger`);
            otherTrigger?.classList.remove('open');
        }
    });

    if (isOpen) {
        submenu.classList.remove('open');
        submenu.style.maxHeight = '0';
        trigger?.classList.remove('open');

        const saved = getSavedGroups().filter(id => id !== groupId);
        saveGroups(saved);
    } else {
        submenu.classList.add('open');
        submenu.style.maxHeight = submenu.scrollHeight + 'px';
        trigger?.classList.add('open');

        const saved = getSavedGroups().filter(id => id !== groupId);
        saved.push(groupId);
        saveGroups(saved);
    }
}

function openGroup(groupId) {
    const submenu = document.getElementById(`submenu-${groupId}`);
    const trigger = document.querySelector(`#group-${groupId} .menu-group-trigger`);
    if (!submenu || submenu.classList.contains('open')) return;

    submenu.classList.add('open');
    submenu.style.maxHeight = submenu.scrollHeight + 'px';
    trigger?.classList.add('open');
}

// ── Marca link ativo e abre grupo pai ───────────────────────
function setActiveMenu() {
    const currentPath = window.location.pathname;

    // Links simples
    document.querySelectorAll('.menu-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });

    // Sublinks — marca ativo e abre o grupo pai
    document.querySelectorAll('.menu-sublink').forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href)) {
            link.classList.add('active');

            // Abre o grupo pai
            const submenu = link.closest('.menu-submenu');
            if (submenu) {
                const groupId = submenu.id.replace('submenu-', '');
                openGroup(groupId);
            }
        }
    });
}

// ── Restaura grupos abertos (persistência de sessão) ─────────
function restoreGroups() {
    getSavedGroups().forEach(groupId => openGroup(groupId));
}

// ── Logout ───────────────────────────────────────────────────
document.querySelector('.logout-btn').addEventListener('click', function () {
    fetch('/logout', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => { if (data.success) window.location.href = '/'; });
});

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initMenu();
    restoreGroups();  // antes do setActive para não conflitar com maxHeight
    setActiveMenu();
});