
const form = document.getElementById('clienteForm');
form.addEventListener('submit', function(e) {
    e.preventDefault();

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
        // Caso erro de validação retornado via throw
        const groupedErrors = data.message;
        let allErrors = flattenGroupedMessages(groupedErrors);
        renderFormMessage(form, allErrors);
        form.reset();
    })
    .catch( error => {
    // Caso erro de validação retornado via throw
    const groupedErrors = error.errors;
    let allErrors = flattenGroupedMessages(groupedErrors);
    renderFormMessage(form, allErrors);

    })
})