const API_BASE = "";

if (!localStorage.getItem("usuarioLogado")) {
    window.location.href = "login.html";
}

document.addEventListener("DOMContentLoaded", async () => {
  const receitaId = localStorage.getItem("receitaIdAtiva");
  const usuarioAtivo = localStorage.getItem("emailUsuarioLogado");
  const campoNomeTopo = document.getElementById("nome-usuario-topo");

  if (campoNomeTopo && usuarioAtivo) {
    campoNomeTopo.innerHTML = ` | <span style=\"font-size: 0.9rem; color: #aaa; font-weight: normal;\">${usuarioAtivo}</span>`;
  }

  if (!receitaId) {
    window.location.href = "receitas.html";
    return;
  }

  await carregarDetalhesComTratamento(receitaId);
});

async function carregarDetalhesComTratamento(receitaId) {
  const tituloElement = document.getElementById("recipe-title");
  
  // Criando um controle de tempo limite (Timeout) de 8 segundos
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 8000);

  try {
    const res = await fetch(`${API_BASE}/api/externa/receita-detalhes/${receitaId}`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (!res.ok) throw new Error(`Status ${res.status}`);

    const receita = await res.json();

    tituloElement.innerText = receita.name;

    const imgElement =
      document.querySelector(".recipe-card__image img") ||
      document.getElementById("recipe-image");
    if (imgElement) imgElement.src = receita.image;

    document.getElementById("recipe-instructions").innerText = receita.instructions;

    const listaIngredientes = document.getElementById("ingredients-list");
    if (listaIngredientes) {
      listaIngredientes.innerHTML = receita.ingredients.map((ing) => `<li>${ing}</li>`).join("\");");
    }
  } catch (error) {
    clearTimeout(timeoutId);
    console.error(error);
    
    // Alerta o usuário visualmente usando seu toast.js
    if (typeof mostrarToast === "function") {
      mostrarToast("O servidor demorou para responder. Tentando reconectar...", "erro");
    }

    // Substitui o "Carregando..." por uma interface de erro amigável na tela
    if (tituloElement) {
      tituloElement.innerHTML = `
        <div style="text-align: center; padding: 20px;">
          <p style="font-size: 1.1rem; color: #e74c3c; margin-bottom: 10px;">Não foi possível carregar a receita.</p>
          <button onclick="window.location.reload()" style="background-color: #ff7f50; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer;">
            <i class="fa-solid fa-rotate-right"></i> Tentar Novamente
          </button>
        </div>
      `;
    }
  }
}