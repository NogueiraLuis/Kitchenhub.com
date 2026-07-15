// static/js/toast.js

function mostrarToast(mensagem, tipo = "sucesso") {
    const container = document.getElementById("toast-container");
    if (!container) {
        console.warn("Aviso: O elemento #toast-container não foi encontrado no HTML.");
        return;
    }

    // 1. Cria o elemento do toast
    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;

    // 2. Escolhe o ícone baseado no tipo
    const icone = tipo === "sucesso" ? "fa-circle-check" : "fa-circle-exclamation";

    // 3. Monta o HTML interno
    toast.innerHTML = `
        <i class="fa-solid ${icone}"></i>
        <span>${mensagem}</span>
    `;

    // 4. CORREÇÃO CRÍTICA: Em vez de appendChild, usamos prepend para injetar 
    // no topo do container isolado, sem mexer na estrutura do fluxo do <main>
    container.prepend(toast);

    // 5. Mantém o balão fixo na tela pelos 3 segundos programados
    setTimeout(() => {
        toast.classList.add("saindo");
        
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}