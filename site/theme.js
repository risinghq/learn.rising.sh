// Se carga en <head> para fijar ambos atributos antes de pintar. Sin modo guardado, sigue la preferencia del sistema.
/* oxlint-disable unicorn/consistent-function-scoping --
   Script clásico en una función: sus ayudas no pueden salir al ámbito global. */
(() => {
  const MODE = "qiskit:theme",
    PAL = "qiskit:paleta";
  const root = document.documentElement;
  // Los textos del control siguen el atributo lang de la página.
  const TEXT = {
    es: {
      paletas: { fosforo: "Fósforo", cobre: "Cobre", medianoche: "Medianoche" },
      palette: "Paleta",
      paletteTitle: "Paleta de colores",
      toggle: "Tema claro u oscuro",
      toDark: "Cambiar a tema oscuro",
      toLight: "Cambiar a tema claro",
    },
    en: {
      paletas: { fosforo: "Phosphor", cobre: "Copper", medianoche: "Midnight" },
      palette: "Palette",
      paletteTitle: "Color palette",
      toggle: "Light or dark theme",
      toDark: "Switch to dark theme",
      toLight: "Switch to light theme",
    },
  };
  const text = () => TEXT[root.lang.slice(0, 2)] ?? TEXT.es;
  const PALETAS = TEXT.es.paletas;
  const read = (k) => {
    try {
      return localStorage.getItem(k);
    } catch {
      return null;
    }
  };
  const write = (k, v) => {
    try {
      localStorage.setItem(k, v);
    } catch {}
  };
  const sys = () =>
    matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";

  const savedMode = read(MODE),
    savedPal = read(PAL);
  root.dataset.theme =
    savedMode === "light" || savedMode === "dark" ? savedMode : sys();
  root.dataset.paleta = Object.hasOwn(PALETAS, savedPal) ? savedPal : "fosforo";

  const modeLabel = () => (root.dataset.theme === "light" ? "☾" : "☀");
  const modeTitle = () =>
    root.dataset.theme === "light" ? text().toDark : text().toLight;
  const paint = () =>
    document.querySelectorAll("[data-theme-ctl]").forEach((c) => {
      c.querySelector("select").value = root.dataset.paleta;
      const b = c.querySelector("button");
      b.textContent = modeLabel();
      b.title = modeTitle();
    });

  window.toggleTheme = () => {
    root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
    write(MODE, root.dataset.theme);
    paint();
    dispatchEvent(new Event("themechange"));
  };
  const setPaleta = (p) => {
    root.dataset.paleta = p;
    write(PAL, p);
    paint();
    dispatchEvent(new Event("themechange"));
  };

  addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-ctl]").forEach((c) => {
      const sel = document.createElement("select");
      sel.setAttribute("aria-label", text().palette);
      sel.title = text().paletteTitle;
      for (const k in PALETAS) sel.add(new Option(text().paletas[k], k));
      sel.addEventListener("change", () => setPaleta(sel.value));
      const btn = document.createElement("button");
      btn.setAttribute("aria-label", text().toggle);
      btn.addEventListener("click", window.toggleTheme);
      c.classList.add("theme-ctl");
      c.append(sel, btn);
    });
    paint();
  });
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => {
    if (read(MODE)) return;
    root.dataset.theme = sys();
    paint();
    dispatchEvent(new Event("themechange"));
  });
})();
