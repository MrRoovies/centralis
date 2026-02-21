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

document.querySelector('.btn').addEventListener('click', function(){
    document.getElementById("errorMessage").style.display = 'none';
    document.getElementById("successMessage").style.display = 'none';

    const form = document.querySelector(".login-container");
    const dados = JSON.stringify({
            'text_user': form.querySelector("#username").value,
            'text_pass': form.querySelector("#password").value
        });
    console.log(dados);
    fetch("/login", {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json'},
        body: dados
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok){ throw data; }
        return data;
    })
    .then( data => {
        document.getElementById("successMessage").style.display = 'block';
        document.getElementById("successMessage").innerText = data.message;
        window.location.href = "/home";
        return;
    })
    .catch(error => {
        document.getElementById("errorMessage").style.display = 'block';
        document.getElementById("errorMessage").innerText = error.message;
    })
})