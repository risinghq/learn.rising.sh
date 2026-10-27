// Se carga en <head> para fijar data-theme antes de pintar. Sin valor guardado, el sistema elige el modo.
/* oxlint-disable unicorn/consistent-function-scoping --
   Script clásico en una función: sus ayudas no pueden salir al ámbito global. */
(() => {
  const MODE = "qiskit:theme";
  const root = document.documentElement;
  // Los textos del control siguen el atributo lang de la página.
  const TEXT = {
    es: { toDark: "Tema oscuro", toLight: "Tema claro" },
    en: { toDark: "Dark theme", toLight: "Light theme" },
  };
  const text = () => TEXT[root.lang.slice(0, 2)] ?? TEXT.es;
  const read = (k) => {
    try {
      return localStorage.getItem(k);
    } catch {
      return null;
    }
  };
  const dark = matchMedia("(prefers-color-scheme: dark)");
  const mode = () => root.dataset.theme ?? (dark.matches ? "dark" : "light");

  const saved = read(MODE);
  if (saved === "light" || saved === "dark") root.dataset.theme = saved;

  const paint = () =>
    document.querySelectorAll("[data-theme-ctl] button").forEach((b) => {
      b.textContent = mode() === "dark" ? text().toLight : text().toDark;
    });

  window.toggleTheme = () => {
    root.dataset.theme = mode() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(MODE, root.dataset.theme);
    } catch {}
    paint();
    dispatchEvent(new Event("themechange"));
  };

  addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-ctl]").forEach((c) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.addEventListener("click", window.toggleTheme);
      c.classList.add("theme-ctl");
      c.append(btn);
    });
    paint();
  });
  dark.addEventListener("change", () => {
    if (root.dataset.theme) return;
    paint();
    dispatchEvent(new Event("themechange"));
  });
})();
