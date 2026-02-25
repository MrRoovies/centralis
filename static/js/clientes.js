
document.addEventListener('click', function(e){
    const btn = e.target.closest(".action-btn");
    if(!btn){ return; }

    e.preventDefault();

    const action = btn.dataset.action;
    const type = btn.dataset.type;
    const id = btn.dataset.cliente;
    const target = btn.dataset.target;

    const delete_form = document.querySelector('#form_del_mail');

    if (action === "delete") {
        fetch(`/clientes/${type}/${id}/${action}`, {
            method: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        })
        .then(async response => {
            const data = await response.json();
            if(!response.ok){ throw data; }
            return data;
        })
        .then( data => {
            console.log(data);
            const allErrors = {};
            const groupedErrors = data.messages;

            for (let formName in groupedErrors) {
                let formErrors = groupedErrors[formName];

                for (let field in formErrors) {
                    allErrors[field] = formErrors[field];
                }
            }
            renderFormMessage(delete_form, allErrors);
        })
        .catch( error => {
            console.log(error);
        })
    }
})

const SystemModal = {
    open(url){
        fetch(url)
        .then(res => res.text())
        .then(async data => {
            document.body.insertAdjacentHTML('beforeend', data);
            this.bindForm(url);
        });
    },

    bindForm(url){
        const form = document.querySelector('#modal_form');
        if (!form) return;

        form.addEventListener('submit', function(e){
            e.preventDefault();
            const formData = new FormData(form);
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
                if(data.success){
                    SystemModal.close();
                    location.reload(); // depois melhoramos isso
                }
                else if(data.state  === "reactivate"){
                    const allErrors = {};
                    const groupedErrors = data.messages;

                    for (let formName in groupedErrors) {
                        let formErrors = groupedErrors[formName];

                        for (let field in formErrors) {
                            allErrors[field] = formErrors[field];
                        }
                    }
                    renderFormMessage(form, allErrors);

                    const btn = document.createElement("button");
                    btn.type = "button";
                    btn.innerText = "Reativar";
                    btn.classList.add("btn-reactivate");
                    btn.classList.add("btn");

                    btn.addEventListener("click", () => {
                        const hidden = document.createElement("input");
                        hidden.type = "hidden";
                        hidden.name = "force_reactivate";
                        hidden.value = "true";
                        form.appendChild(hidden);

                        form.requestSubmit();
                    });

                    form.prepend(btn);
                }
                else {
                    // remove modal antigo
                    SystemModal.close();
                    // insere novo com erros
                    document.body.insertAdjacentHTML('beforeend', data.html);
                    SystemModal.bindForm(url);
                }
            })
            .catch(error => {
                const allErrors = {};
                const groupedErrors = error.errors;

                for (let formName in groupedErrors) {
                    let formErrors = groupedErrors[formName];

                    for (let field in formErrors) {
                        allErrors[field] = formErrors[field];
                    }
                }

                renderFormMessage(form, allErrors);
             });
        });
    },

    close(){
        document.getElementById('sys-modal')?.remove();
        document.getElementById('sys-modal-overlay')?.remove();
    }
};
