const API_BASE = "";

if (!localStorage.getItem("usuario_id")) {
    window.location.href = "login.html";
}

let todasAsReceitasSalvas = [];

document.addEventListener("DOMContentLoaded", async () => {
  const usuarioAtivo = localStorage.getItem("emailUsuarioLogado");
  const campoNomeTopo = document.getElementById("nome-usuario-topo");

  if (campoNomeTopo && usuarioAtivo) {
    campoNomeTopo.innerHTML = ` | <span class="user-email-topo">${usuarioAtivo}</span>`;
  }

  await buscarReceitasDoBanco();
});

async function buscarReceitasDoBanco() {
  const idUsuarioAtivo = localStorage.getItem("usuario_id");
  const vitrine = document.getElementById("recipe-grid");

  if (!idUsuarioAtivo || idUsuarioAtivo === "null" || idUsuarioAtivo === "undefined") {
    todasAsReceitasSalvas = [];
    if (vitrine) {
      vitrine.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 40px 20px;">
          <p style="font-size: 1.3rem; color: #e0e0e0; margin-bottom: 15px;">Você não está conectado!</p>
          <p style="color: #aaa; margin-bottom: 20px;">Para ver o seu livro de receitas, faça login.</p>
          <a href="login.html" style="background-color: #ff7f50; color: white; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: bold;">Fazer Login</a>
        </div>
      `;
    }
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/meu-livro/${idUsuarioAtivo}`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    todasAsReceitasSalvas = await res.json();
    renderizarCards(todasAsReceitasSalvas);
  } catch {
    mostrarToast("Erro ao carregar o livro de receitas.", "erro");
  }
}

function renderizarCards(listaDeReceitas) {
  const vitrine = document.getElementById("recipe-grid");
  vitrine.innerHTML = "";

  if (!listaDeReceitas || listaDeReceitas.length === 0) {
    vitrine.innerHTML =
      "<p style='color: #ffffff; grid-column: 1/-1; text-align: center;'>Nenhuma receita encontrada para este filtro.</p>";
    return;
  }

  listaDeReceitas.forEach((receita) => {
    const tituloEscapado = receita.titulo.replace(/'/g, "\\'");
    const card = document.createElement("article");
    card.className = "recipe-card";
    card.innerHTML = `
      <figure class="recipe-card__image">
        <img src="${receita.imagem}" alt="Foto de ${receita.titulo}" />
      </figure>
      <div class="recipe-card__info">
        <h2>${receita.titulo}</h2>
        <p style="color: white">Prato Salvo no Livro</p>
        <div class="ver-receita-fav">
          <button type="button" class="ver_receita" onclick="irParaDetalhes('${receita.external_id}')">
            <p style="pointer-events: none;"><strong>Ver receita</strong></p>
          </button>
          <button type="button" class="remover_receita" onclick="removerDoBanco(event, ${receita.id}, '${tituloEscapado}')">
            <p style="pointer-events: none;"><strong>Excluir</strong></p>
          </button>
        </div>
      </div>
    `;
    vitrine.appendChild(card);
  });
}

function filtrarCategoria(codigoCategoria) {
  if (codigoCategoria === "todas") {
    renderizarCards(todasAsReceitasSalvas);
    return;
  }
  renderizarCards(todasAsReceitasSalvas.filter((r) => r.tempo === codigoCategoria));
}

function irParaDetalhes(id) {
  localStorage.setItem("receitaIdAtiva", String(id));
  window.location.href = "info-receita.html";
}

async function removerDoBanco(evento, idBanco, titulo) {
  evento.preventDefault();
  evento.stopPropagation();

  const container = document.getElementById("toast-container");
  if (!container) return;

  const toastConfirmacao = document.createElement("div");
  toastConfirmacao.className = "toast erro";
  toastConfirmacao.style.flexDirection = "column";
  toastConfirmacao.style.alignItems = "flex-start";
  toastConfirmacao.innerHTML = `
    <div style="display: flex; gap: 12px; align-items: center;">
      <i class="fa-solid fa-circle-exclamation"></i>
      <span>Remover "${titulo}"?</span>
    </div>
    <div style="display: flex; gap: 10px; margin-top: 12px; width: 100%; justify-content: flex-end;">
      <button id="btn-toast-sim" style="background-color: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer;">Sim</button>
      <button id="btn-toast-nao" style="background-color: #7f8c8d; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">Não</button>
    </div>
  `;
  container.prepend(toastConfirmacao);

  toastConfirmacao.querySelector("#btn-toast-nao").onclick = () => {
    toastConfirmacao.classList.add("saindo");
    setTimeout(() => toastConfirmacao.remove(), 300);
  };

  toastConfirmacao.querySelector("#btn-toast-sim").onclick = async () => {
    toastConfirmacao.remove();
    try {
      const res = await fetch(`${API_BASE}/api/meu-livro/${idBanco}`, { method: "DELETE" });
      if (res.ok) {
        todasAsReceitasSalvas = todasAsReceitasSalvas.filter((r) => r.id !== idBanco);
        const card = evento.target.closest("article");
        if (card) card.remove();
        mostrarToast(`"${titulo}" foi removida do seu livro.`, "sucesso");
        if (todasAsReceitasSalvas.length === 0) {
          document.getElementById("recipe-grid").innerHTML =
            "<p style='color: #ffffff; grid-column: 1/-1; text-align: center;'>Nenhuma receita encontrada para este filtro.</p>";
        }
      } else {
        mostrarToast("Não foi possível remover a receita.", "erro");
      }
    } catch {
      mostrarToast("Erro de conexão com o servidor.", "erro");
    }
  };
}

function fazerLogout() {
  localStorage.removeItem("usuario_id");
  localStorage.removeItem("emailUsuarioLogado");
  mostrarToast("Você saiu da sua conta.", "sucesso");
  setTimeout(() => { window.location.href = "index.html"; }, 1200);
}
