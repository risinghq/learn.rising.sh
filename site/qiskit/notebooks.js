// El sitio publicado enlaza al repositorio porque el lector no tiene sus archivos locales.
window.notebookHelp = (parent) => {
  const p = document.createElement("p");
  p.className = "mhow";
  p.append("Cómo ejecutar los cuadernos: clona el ");
  const a = document.createElement("a");
  a.href = "https://github.com/risinghq/duo";
  a.target = "_blank";
  a.rel = "noopener";
  a.textContent = "repositorio";
  p.append(a, " y sigue «Instalar» en su README.");
  parent.appendChild(p);
  return p;
};
