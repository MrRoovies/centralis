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
            console.log(error);
        })
    }
})


// Objeto responsável por gerenciar modais do sistema
const SystemModal = {
    // Abre modal carregando HTML via fetch
    open(url){
        fetch(url)
        .then(res => res.text())
        // Injeta o HTML do modal no final do body
        .then(async data => {
            document.body.insertAdjacentHTML('beforeend', data);
            // Faz bind do formulário dentro do modal
            this.bindForm(url);
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
                const groupedErrors = error.errors;
                let allErrors = flattenGroupedMessages(groupedErrors);
                renderFormMessage(form, allErrors);
             });
        });
    },
    // Fecha modal removendo elementos do DOM
    close(){
        document.getElementById('sys-modal')?.remove();
        document.getElementById('sys-modal-overlay')?.remove();
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
            allErrors[field] = formErrors[field];
        }
    }

    return allErrors;
}