const show_error = (text) => {
    let error = document.querySelector('#error_box');
        error.querySelector("#error_message").innerText = text;
        error.style.opacity = 1;
        error.style.transform = 'translate(-50%, 0%)';

    setTimeout(() => {
        error.style.opacity = 0;
        error.style.transform = 'translate(-50%, -100%)';
    }, 5000);
}