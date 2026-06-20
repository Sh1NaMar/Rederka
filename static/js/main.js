// Глобальный хелпер для CSRF и тостов (если нужно)
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

window.showToast = function(message, isError = false) {
    const toastEl = document.getElementById('liveToast');
    if (!toastEl) return;
    const toast = new bootstrap.Toast(toastEl);
    const toastBody = toastEl.querySelector('.toast-body');
    toastBody.innerHTML = message;
    toastEl.classList.toggle('bg-danger', isError);
    toast.show();
    setTimeout(() => toastEl.classList.remove('bg-danger'), 5000);
};

