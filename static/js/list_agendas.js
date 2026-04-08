
function abrirAcionamentos(agendaId) {
    const overlay = document.getElementById('al-drawer-overlay');
    const drawer  = document.getElementById('al-drawer');
    const body    = document.getElementById('al-drawer-body');
    const info    = document.getElementById('al-drawer-agenda-info');
    const sub     = document.getElementById('al-drawer-subtitle');

    overlay.classList.add('active');
    drawer.classList.add('active');
    body.innerHTML  = '<div class="al-spinner-wrap"><div class="al-spinner"></div></div>';
    info.innerHTML  = '';
    sub.textContent = '';

    fetch(`/relatorios/acionamentos/${agendaId}/`)
        .then(r => r.json())
        .then(data => {

            sub.textContent = data.cliente;

            info.innerHTML = `
                <div class="al-agenda-meta">
                    <div class="al-agenda-meta__item">
                        <span>Agente</span>
                        <strong>${data.agente}</strong>
                    </div>
                    <div class="al-agenda-meta__item">
                        <span>Carteira</span>
                        <strong>${data.carteira}</strong>
                    </div>
                    <div class="al-agenda-meta__item">
                        <span>Canal</span>
                        <strong>${data.canal}</strong>
                    </div>
                    <div class="al-agenda-meta__item">
                        <span>Situação Atual</span>
                        <strong>${data.situacao_atual}</strong>
                    </div>
                    <div class="al-agenda-meta__item">
                        <span>Status</span>
                        <strong class="${data.ativa ? 'al-txt-ativa' : 'al-txt-finalizada'}">
                            ${data.ativa ? 'Ativa' : 'Finalizada'}
                        </strong>
                    </div>
                    ${data.retorno ? `
                    <div class="al-agenda-meta__item">
                        <span>Retorno</span>
                        <strong>${data.retorno}</strong>
                    </div>` : ''}
                </div>
            `;

            if (!data.acionamentos.length) {
                body.innerHTML = `
                    <div class="al-timeline-empty">
                        <span>Nenhum acionamento registrado</span>
                    </div>`;
                return;
            }

            body.innerHTML = `
                <div class="al-timeline">
                    ${data.acionamentos.map((a, i) => `
                        <div class="al-tl-item ${i === 0 ? 'al-tl-item--last' : ''}">
                            <div class="al-tl-dot al-tl-dot--${a.tipo}"></div>
                            <div class="al-tl-content">
                                <div class="al-tl-header">
                                    <span class="al-tl-badge al-tl-badge--${a.tipo}">
                                        ${a.situacao}
                                    </span>
                                    <span class="al-tl-tempo">${a.tempo_tela}</span>
                                </div>
                                <div class="al-tl-datas">
                                    <span>⏱ ${a.inicio}</span>
                                    ${a.fim ? `<span>→ ${a.fim}</span>` : '<span class="al-tl-aberto">em aberto</span>'}
                                </div>
                                ${a.comentario
                                    ? `<p class="al-tl-coment">"${a.comentario}"</p>`
                                    : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        })
        .catch(() => {
            body.innerHTML = `
                <div class="al-timeline-empty" style="color:#c33">
                    Erro ao carregar acionamentos.
                </div>`;
        });
}

function fecharAcionamentos() {
    document.getElementById('al-drawer-overlay').classList.remove('active');
    document.getElementById('al-drawer').classList.remove('active');
}

// fecha com ESC
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') fecharAcionamentos();
});