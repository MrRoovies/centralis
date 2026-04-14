
// ── Toggle edição ──────────────────────────────────────────
function toggleEdit(formId, btn) {
    const form    = document.getElementById(formId);
    const readId  = formId.replace('Form', 'Read');
    const readEl  = document.getElementById(readId);
    const isOpen  = form.style.display !== 'none';

    form.style.display  = isOpen ? 'none'  : 'block';
    if (readEl)
        readEl.style.display = isOpen ? '' : 'none';
    btn.textContent     = isOpen ? 'Editar' : 'Cancelar';
    btn.classList.toggle('vd-edit-toggle--active', !isOpen);

    // ao abrir o form de oferta, carrega a cascata pré-selecionada
    if (!isOpen && formId === 'ofertaForm') {
        initVendaForm();

    }
}

// ── Salvar Valores ────────────────────────────────────────
function salvarValores(e) {
    e.preventDefault();
    const form = document.getElementById('valoresForm');
    const data = Object.fromEntries(new FormData(form));

    fetch(`/relatorios/${VENDA_ID}/valores/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': data.csrfmiddlewaretoken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const groupedMessages = d.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);

        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
    })
    .catch(err => {
        const groupedMessages = err.messages;
        const allMessages = flattenGroupedMessages(groupedMessages);
        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
    });
}

// ── Salvar Esteira/Agente ─────────────────────────────────
function salvarResponsavel(e) {
    e.preventDefault();
    const form = document.getElementById('responsavelForm');
    const data = Object.fromEntries(new FormData(form));

    fetch(`/relatorios/${VENDA_ID}/responsavel/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': data.csrfmiddlewaretoken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const groupedMessages = d.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);

        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
    })
    .catch(err => {
        const groupedMessages = err.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);

        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
    });
}

// ── Adicionar Comentário / HistVenda ─────────────────────
function Comentario_e_esteira(e) {
    e.preventDefault();
    const form = document.getElementById('comentarioForm');
    const data = Object.fromEntries(new FormData(form));

    const btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    btn.textContent = 'Salvando...';

    fetch(`/relatorios/${VENDA_ID}/comentario_e_esteira/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': data.csrfmiddlewaretoken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        let allMessages = flattenGroupedMessages(d.messages);
        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);

        // injeta novo item no topo da timeline sem reload
        /*
        if (d.html) {
            const container = document.getElementById('timelineContainer');
            container.innerHTML = d.html;
        }
        */
    })
    .catch(err => {
        const groupedMessages = err.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);

        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
    })
    .finally(() => {
        btn.disabled = false;
        btn.textContent = 'Registrar';
    });
}

// ── Salvar Oferta ─────────────────────────────────────────
function salvarOferta(e) {
    e.preventDefault();
    const form = document.getElementById('ofertaForm');
    const data = Object.fromEntries(new FormData(form));

    fetch(`/relatorios/${VENDA_ID}/oferta/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': data.csrfmiddlewaretoken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(async r => { const d = await r.json(); if (!r.ok) throw d; return d; })
    .then(d => {
        const groupedMessages = d.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);

        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
        /*
        // atualiza leitura sem reload
        document.getElementById('read-produto').textContent  = d.produto_nome;
        document.getElementById('read-parceiro').textContent = d.parceiro_nome;
        document.getElementById('read-comissao').textContent = d.comissao + '%';
        // atualiza estado local para re-abrir corretamente
        OFERTA_ATUAL.parceiro_id = data.parceiro;
        OFERTA_ATUAL.produto_id  = data.produto;
        OFERTA_ATUAL.oferta_id   = data.oferta;
        */
    })
    .catch(err => {
        const groupedMessages = err.messages;
        let allMessages = flattenGroupedMessages(groupedMessages);

        // Renderiza mensagens no formulário
        renderFormMessage(form, allMessages);
    });
}