const API_BASE = "";

const cadastro = document.querySelector("#criar-conta");
const trocarLogin = document.querySelector("#cadastro");
const telaLogin = document.querySelector(".login");
const voltarLogin = document.querySelector("#voltar-login");

if (cadastro) {
  cadastro.addEventListener("click", (e) => {
    e.preventDefault();
    telaLogin.style.display = "none";
    trocarLogin.style.display = "flex";
  });
}

if (voltarLogin) {
  voltarLogin.addEventListener("click", (e) => {
    e.preventDefault();
    trocarLogin.style.display = "none";
    telaLogin.style.display = "flex";
  });
}

document.querySelector("#form-cadastro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.querySelector("#cad-email").value.trim();
  const senha = document.querySelector("#cad-senha").value;

  try {
    const res = await fetch(`${API_BASE}/api/usuario/cadastro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    const dados = await res.json();
    if (res.ok) {
      mostrarToast("Conta criada com sucesso!", "sucesso");
      // CORREÇÃO AQUI: Gravando a chave correta que os outros scripts procuram
      localStorage.setItem("usuario_id", dados.usuario_id);
      localStorage.setItem("emailUsuarioLogado", dados.usuario);
      setTimeout(() => { window.location.href = "sessoes.html"; }, 1500);
    } else {
      mostrarToast(dados.detail || "Erro ao tentar cadastrar.", "erro");
    }
  } catch {
    mostrarToast("Não foi possível conectar ao servidor.", "erro");
  }
});

document.querySelector("#form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.querySelector("#log-email").value.trim();
  const senha = document.querySelector("#log-senha").value;

  try {
    const res = await fetch(`${API_BASE}/api/usuario/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    const dados = await res.json();
    if (res.ok) {
      // CORREÇÃO AQUI: Gravando a chave correta que os outros scripts procuram
      localStorage.setItem("usuario_id", dados.usuario_id);
      localStorage.setItem("emailUsuarioLogado", dados.usuario);
      mostrarToast("Login efetuado com sucesso!", "sucesso");
      setTimeout(() => { window.location.href = "sessoes.html"; }, 1500);
    } else {
      mostrarToast(dados.detail || "Usuário ou senha incorretos.", "erro");
    }
  } catch {
    mostrarToast("Não foi possível conectar ao servidor.", "erro");
  }
});

function fazerLogout() {
  localStorage.removeItem("usuario_id");
  localStorage.removeItem("emailUsuarioLogado");
  window.location.href = "login.html";
}