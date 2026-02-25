
const form = document.getElementById('clienteForm');
form.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(form);

    fetch("/clientes/cliente_novo", {
        method: "POST",
        body: new FormData(form)
    })
    .then( async response => {
        const data = await response.json();
        if(!response.ok){ throw data; }
        return data;
    })
    .then( data  => {
        renderFormMessage(form, data.message, "success");
        form.reset();
    })
    .catch( error => {

        const allErrors = {};
        const groupedErrors = error.errors;

        for (let formName in groupedErrors) {
            let formErrors = groupedErrors[formName];

            for (let field in formErrors) {
                allErrors[field] = formErrors[field];
            }
        }

        renderFormErrors(form, allErrors);

    })
})