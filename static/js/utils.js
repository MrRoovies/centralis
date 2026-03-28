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

// Objeto responsável por gerenciar modais do sistema
const SystemModal = {
    // Abre modal carregando HTML via fetch
    open(url){
        fetch(url)
        .then(res => {
            if(!res.ok){ throw new Error("Erro ao carregar formulário"); }
            return res.text();
        })
        // Injeta o HTML do modal no final do body
        .then(data => {
            document.body.insertAdjacentHTML('beforeend', data);
            // Faz bind do formulário dentro do modal
            this.bindForm(url);
        })
            .catch(error => {
            alert(error.message); // ou um feedback mais elegante
        });
    },

    // Vincula evento de submit ao formulário do modal
    bindForm(url){
        const form = document.querySelector('#modal_form');
        if (!form) return;

        form.addEventListener('submit', function(e){
            e.preventDefault();
            const formData = new FormData(form);

            // Envia dados do formulário via POST
            fetch(url, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": form.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then( async response =>{
                const data = await response.json();
                if (!response.ok){ throw data; }
                return data;
             })
            .then( data => {
                // Caso sucesso total
                if(data.success){
                    SystemModal.close();
                    location.reload(); // TODO: melhorar para evitar reload
                }
                // Caso backend peça confirmação de reativação
                else if(data.state  === "reactivate"){
                    // Agrupa erros/mensagens de múltiplos forms
                    const groupedMessages = data.messages;
                    let allMessages = flattenGroupedMessages(groupedMessages);
                    renderFormMessage(form, allMessages);

                    // Cria botão dinâmico de reativação
                    const btn = document.createElement("button");
                    btn.type = "button";
                    btn.innerText = "Reativar";
                    btn.classList.add("btn-reactivate");
                    btn.classList.add("btn");

                    // Ao clicar, injeta campo hidden forçando reativação
                    btn.addEventListener("click", () => {
                        const hidden = document.createElement("input");
                        hidden.type = "hidden";
                        hidden.name = "force_reactivate";
                        hidden.value = "true";
                        form.appendChild(hidden);

                        form.requestSubmit();
                    });

                    // Insere botão no topo do formulário
                    form.prepend(btn);
                }
                // Caso erro validado pelo backend
                else {
                    // remove modal antigo
                    SystemModal.close();
                    // insere novo com erros
                    document.body.insertAdjacentHTML('beforeend', data.html);
                    // Rebind do form
                    SystemModal.bindForm(url);
                }
            })
            .catch(error => {
                // Caso erro de validação retornado via throw
                const groupedErrors = error.messages;
                let allErrors = flattenGroupedMessages(groupedErrors);
                renderFormMessage(form, allErrors);
             });
        });
    },
    // Fecha modal removendo elementos do DOM
    close(){
        document.getElementById('sys-modal')?.remove();
        document.getElementById('sys-modal-overlay')?.remove();
    },

    showMessage(groupedMessages){
        const MESSAGE_TYPE_MAP = {
            error: 'error',      // ou 'warning' se quiser suavizar
            warning: 'warning',
            success: 'success',
            info: 'info'
        };

        const allMessages = flattenGroupedMessages(groupedMessages);
        let html = `
            <div class="modal-overlay" id="sys-modal-overlay"></div>
            <div class="modal" id="sys-modal">
                <div class="modal-body">`;

        for (const type in allMessages) {
            const cssType = MESSAGE_TYPE_MAP[type] || 'info';
            allMessages[type].forEach(msg => {
                html += `
                    <div class="cliente-form ${cssType}-message" style="display:block">
                        <div class="alert">${msg}</div>
                    </div>`;
            });
        }

        html += `
                </div>
                <div class="modal-footer" id="sys-modal-footer">
                    <button class="btn-small btn-delete" onclick="SystemModal.close()">Fechar</button>
                </div>
            </div>`;

            document.body.insertAdjacentHTML('beforeend', html);
    }
};

/**
 * Recebe um objeto de erros agrupados por formulário
 * no formato:
 * {
 *   form1: { campo1: ["erro1"], campo2: ["erro2"] },
 *   form2: { campo3: ["erro3"] }
 * }
 *
 * E transforma em um único objeto plano:
 * {
 *   campo1: ["erro1"],
 *   campo2: ["erro2"],
 *   campo3: ["erro3"]
 * }
 *
 * Isso é necessário porque o backend pode retornar
 * múltiplos forms com erros separados, mas o frontend
 * precisa renderizar tudo em um único formulário visível.
 */
function flattenGroupedMessages(groupedErrors) {

    const allErrors = {}; // objeto final que conterá todos os erros "achatados"

    // Percorre cada formulário retornado pelo backend
    for (let formName in groupedErrors) {

        // Erros específicos daquele formulário
        let formErrors = groupedErrors[formName];

        // Percorre cada campo com erro dentro do form
        for (let field in formErrors) {

            /**
             * Aqui estamos "achatando" a estrutura:
             * groupedErrors[formName][field]
             * vira:
             * allErrors[field]
             *
             * Se dois forms tiverem o mesmo field,
             * o último sobrescreve (caso queira evitar isso,
             * podemos concatenar arrays).
             */
            if(!allErrors[field]) {
                allErrors[field] = [];
            }
            allErrors[field] = allErrors[field].concat(formErrors[field]);
        }
    }
    return allErrors;
}