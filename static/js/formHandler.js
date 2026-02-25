function renderFormMessage(form, errors) {

    // Remove erros antigos
    form.querySelectorAll(".error-message").forEach(el => el.remove());
    form.querySelectorAll(".warning-message").forEach(el => el.remove());
    form.querySelectorAll(".success-message").forEach(el => el.remove());
    form.querySelectorAll(".input-error").forEach(el => el.classList.remove("input-error"));

    Object.entries(errors).forEach(([field, messages]) => {

        messages.forEach(message => {
            if (field === "warning") {
                const warningBox = document.createElement("div");
                warningBox.classList.add("warning-message");
                warningBox.style.display = "block";
                warningBox.innerText = message;

                form.prepend(warningBox);
            }

            else if (field === "success") {
                const successgBox = document.createElement("div");
                successgBox.classList.add("success-message");
                successgBox.style.display = "block";
                successgBox.innerText = message;

                form.prepend(successgBox);
            }

            else if (field === "__all__") {

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