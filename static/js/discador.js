function verificarChamada(){
    const form_fones = document.getElementById('form_del_telefone');
    console.log(
        form_fones.textContent
    );
    // const contact_items = form_fones.querySelectorAll('.ci-contact-item');
    // console.log(contact_items);
    // contact_items.forEach( div => {
    //     const telefone = div.querySelector('.ci-contact-item__value');
    //     alert(telefone.textContent.trim());
    // })    
}

verificarChamada();