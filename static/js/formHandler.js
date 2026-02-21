function renderFormErrors(form, errors) {

    // Remove erros antigos
    form.querySelectorAll(".error-message").forEach(el => el.remove());
    form.querySelectorAll(".success-message").forEach(el => el.remove());
    form.querySelectorAll(".input-error").forEach(el => el.classList.remove("input-error"));

    Object.entries(errors).forEach(([field, messages]) => {

        messages.forEach(message => {

            if (field === "__all__") {

                const errorBox = document.createElement("div");
                errorBox.classList.add("error-message");
                errorBox.style.display = "block";
                errorBox.innerText = message;

                form.prepend(errorBox);

            } else {

                const input = form.querySelector(`[name$="-${field}"]`);

                if (input) {

                    input.classList.add("input-error");

                    const error = document.createElement("small");
                    error.classList.add("error-message");
                    error.style.display = "block";
                    error.innerText = message;

                    input.parentElement.appendChild(error);
                }
            }

        });
    });
}

function renderFormMessage(form, message, type = "error") {

    // Remove mensagens antigas
    form.querySelectorAll(".error-message, .success-message")
        .forEach(el => el.remove());

    const box = document.createElement("div");

    if (type === "success") {
        box.classList.add("success-message");
        box.style.display = "block";
    } else {
        box.classList.add("error-message");
        box.style.display = "block";
    }

    box.innerText = message;

    form.prepend(box);
}
