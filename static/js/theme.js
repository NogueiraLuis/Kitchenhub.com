const API_BASE = "";

const NOMES_CATEGORIAS = {
  japonesa: "Culinária Japonesa",
  massa: "Massas Italianas",
  pizza: "Pizzas Artesanais",
  sobremesa: "Sobremesas Especiais",
};

const MAPA_CATEGORIAS = { massa: 1, sobremesa: 2, japonesa: 3, pizza: 4 };

document.addEventListener("DOMContentLoaded", async () => {
  const escolha = localStorage.getItem("sessaoEscolhida");
  const mainCorpo = document.querySelector("main");
  const tituloPagina = document.getElementById("title-theme");
  const usuarioAtivo = localStorage.getItem("emailUsuarioLogado");
  const campoNomeTopo = document.getElementById("nome-usuario-topo");

  if (campoNomeTopo && usuarioAtivo) {
    campoNomeTopo.innerHTML = ` | <span class="user-email-topo">${usuarioAtivo}</span>`;
  }

  if (escolha) {
    if (mainCorpo) mainCorpo.id = escolha;
    if (tituloPagina) {
      tituloPagina.innerText = NOMES_CATEGORIAS[escolha] || "Nossas Receitas";
    }
    await carregarSugestoes(escolha);
  }
});

function irParaDetalhes(id) {
  localStorage.setItem("receitaIdAtiva", String(id));
  window.location.href = "info-receita.html";
}

function abrirModal() {
  document.getElementById("modal-login").style.display = "flex";
}

function fecharModal() {
  document.getElementById("modal-login").style.display = "none";
}

function irParaLogin() {
  window.location.href = "login.html";
}

async function salvarNoBanco(evento, idMeal, strMeal, strMealThumb) {
  evento.preventDefault();
  evento.stopPropagation();

  const idUsuarioAtivo = localStorage.getItem("usuarioLogado");
  if (!idUsuarioAtivo || idUsuarioAtivo === "undefined" || idUsuarioAtivo === "null") {
    abrirModal();
    return;
  }

  try {
    const categoriaAtual = localStorage.getItem("sessaoEscolhida");
    const res = await fetch(`${API_BASE}/api/meu-livro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        external_id: parseInt(idMeal),
        titulo: strMeal,
        imagem: strMealThumb,
        serve: 0,
        tempo: MAPA_CATEGORIAS[categoriaAtual] || 0,
        usuario_id: parseInt(idUsuarioAtivo),
      }),
    });

    if (res.ok) {
      mostrarToast(`"${strMeal}" foi salva no seu livro!`, "sucesso");
    } else {
      mostrarToast("Erro ao tentar favoritar a receita.", "erro");
    }
  } catch {
    mostrarToast("Não foi possível conectar ao servidor.", "erro");
  }
}

async function carregarSugestoes(categoriaEscolhida) {
  const vitrine = document.getElementById("recipe-grid");
  if (!vitrine) return;

  vitrine.innerHTML = "<p>Carregando receitas...</p>";

  try {
    const res = await fetch(`${API_BASE}/api/externa/receitas?categoria=${categoriaEscolhida}`);
    const receitas = await res.json();

    vitrine.innerHTML = "";

    if (!receitas || receitas.length === 0) {
      vitrine.innerHTML = "<p>Nenhuma receita encontrada para esta categoria.</p>";
      return;
    }

    receitas.forEach((receita) => {
      const tituloEscapado = receita.strMeal.replace(/'/g, "\\'");
      const card = document.createElement("article");
      card.className = "recipe-card";
      card.innerHTML = `
        <figure class="recipe-card__image">
          <img src="${receita.strMealThumb}" alt="Foto de ${receita.strMeal}" loading="lazy" />
        </figure>
        <div class="recipe-card__info">
          <h2>${receita.strMeal}</h2>
          <p>Prato Tradicional</p>
          <div class="ver-receita-fav">
            <button type="button" class="ver_receita" onclick="irParaDetalhes('${receita.idMeal}')">
              <p><strong>Ver receita</strong></p>
            </button>
            <button type="button" class="salvar_receita" onclick="salvarNoBanco(event, '${receita.idMeal}', '${tituloEscapado}', '${receita.strMealThumb}')">
              <p><strong>Salvar</strong></p>
            </button>
          </div>
        </div>
      `;
      vitrine.appendChild(card);
    });
  } catch {
    mostrarToast("Erro ao carregar receitas.", "erro");
  }
}

function fazerLogout() {
  localStorage.removeItem("usuarioLogado");
  localStorage.removeItem("emailUsuarioLogado");
  mostrarToast("Você saiu da sua conta.", "sucesso");
  setTimeout(() => { window.location.href = "index.html"; }, 1200);
}
