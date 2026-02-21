
const form = document.getElementById('clienteForm');
form.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(form);

    fetch("cliente_novo", {
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
        console.log("Erro ", error);
        renderFormErrors(form, error.errors);
    })
})