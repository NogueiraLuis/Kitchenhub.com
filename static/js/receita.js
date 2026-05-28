const API_BASE = "";

document.addEventListener("DOMContentLoaded", async () => {
  const receitaId = localStorage.getItem("receitaIdAtiva");
  const usuarioAtivo = localStorage.getItem("emailUsuarioLogado");
  const campoNomeTopo = document.getElementById("nome-usuario-topo");

  if (campoNomeTopo && usuarioAtivo) {
    campoNomeTopo.innerHTML = ` | <span style="font-size: 0.9rem; color: #aaa; font-weight: normal;">${usuarioAtivo}</span>`;
  }

  if (!receitaId) {
    window.location.href = "receitas.html";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/externa/receita-detalhes/${receitaId}`);
    if (!res.ok) throw new Error(`Status ${res.status}`);

    const receita = await res.json();

    document.getElementById("recipe-title").innerText = receita.name;

    const imgElement =
      document.querySelector(".recipe-card__image img") ||
      document.getElementById("recipe-image");
    if (imgElement) imgElement.src = receita.image;

    document.getElementById("recipe-instructions").innerText = receita.instructions;

    const listaIngredientes = document.getElementById("ingredients-list");
    if (listaIngredientes) {
      listaIngredientes.innerHTML = receita.ingredients.map((ing) => `<li>${ing}</li>`).join("");
    }
  } catch {
    document.getElementById("recipe-title").innerText = "Erro ao carregar a receita.";
  }
});
