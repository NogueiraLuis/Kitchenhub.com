// static/js/menuhamb.js

// Seleção de elementos
const btnMenu = document.getElementById("btn-menu");
const btnFechar = document.getElementById("btn-fechar");
const menuLateral = document.getElementById("menu-lateral");

// Função para Alternar Menu
const toggleMenu = (abrir = true) => {
  menuLateral.classList.toggle("ativo", abrir);
  btnMenu.setAttribute("aria-expanded", abrir);
};

// Eventos Simples
btnMenu.addEventListener("click", () => toggleMenu(true));
btnFechar.addEventListener("click", () => toggleMenu(false));

// FECHAR AO CLICAR FORA
document.addEventListener("click", (evento) => {
  const clicouFora = !menuLateral.contains(evento.target);
  const clicouNoBotaoAbrir = btnMenu.contains(evento.target);
  const menuEstaAberto = menuLateral.classList.contains("ativo");

  if (clicouFora && !clicouNoBotaoAbrir && menuEstaAberto) {
    toggleMenu(false);
  }
});

// FECHAR COM A TECLA ESC
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape" && menuLateral.classList.contains("ativo")) {
    toggleMenu(false);
  }
});

// TRAVA EXTRA: Evita que pressionar Enter no campo de busca recarregue a página
const campoBusca = document.getElementById("search-recipe");
if (campoBusca) {
  campoBusca.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
    }
  });
}