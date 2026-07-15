const tema = document.querySelectorAll(".card-section");

function sectionStorage(idDaSessao) {
  localStorage.setItem("sessaoEscolhida", idDaSessao);
  window.location.href = "receitas.html";
}

tema.forEach((card) => {
  card.addEventListener("click", () => {
    sectionStorage(card.id);
  });
});
