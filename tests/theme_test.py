"""Test the shared theme with Playwright on site/ served by http.server.

    uv run --group tools python tests/theme_test.py [--shots FOLDER] [--table]

Load the front page and three lessons (first and last step) in each mode, at
1366x768 and 390x844. Require: no error output in the console, no
`#scene > .blk` outside `#stage`, the same brand and fonts on both pages, the
mode stored exactly once, WCAG AA contrast for each text token and each control
border, and the front page requesting the lesson.json files in parallel.
--shots saves a screenshot per page, mode and size. --table prints the minimum
contrasts as Markdown.
"""

import argparse
import json
import re
import sys
import threading
import time
from collections.abc import Sequence
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from offline import new_context, verify
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

SITE = Path(__file__).resolve().parent.parent / "site"
MODOS = ["dark", "light"]
TAMANOS = {"1366x768": (1366, 768), "390x844": (390, 844)}
LECCIONES = ["p1-quickstart", "p3-target", "p6-panorama"]

TEXTO = ["ink", "muted", "acc-text", "gold", "red", "blue", "teal", "violet", "green"]
SUPERFICIES = ["bg", "bg2", "card", "stage"]
GRAFICOS = ["axis", "wire", "edge"]
DEMORA_LESSON_JSON = 0.4


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        if self.path.endswith("/lesson.json"):
            time.sleep(DEMORA_LESSON_JSON)
        super().do_GET()


def serve() -> tuple[ThreadingHTTPServer, str]:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(SITE)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def luminancia(rgb: Sequence[float]) -> float:
    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: Sequence[float], b: Sequence[float]) -> float:
    x, y = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def parse_color(s: str) -> tuple[float, ...]:
    m = re.match(r"rgba?\(([^)]*)\)", s)
    if m:
        return tuple(float(v) for v in re.split(r"[ ,/]+", m.group(1).strip())[:3])
    m = re.match(r"color\(srgb ([^)]*)\)", s)
    if m:
        return tuple(float(v) * 255 for v in m.group(1).split()[:3])
    raise ValueError(s)


RESOLVER = """names => {
  const probe = document.createElement('span');
  document.body.appendChild(probe);
  const px = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const out = {};
  for (const n of names) {
    probe.style.color = `var(--${n})`;
    px.clearRect(0, 0, 1, 1);
    px.fillStyle = getComputedStyle(probe).color;
    px.fillRect(0, 0, 1, 1);
    out[n] = `rgb(${px.getImageData(0, 0, 1, 1).data.slice(0, 3).join(' ')})`;
  }
  probe.remove();
  return out;
}"""


class Report:
    def __init__(self) -> None:
        self.fallos: list[str] = []
        self.pruebas = 0

    def check(self, ok: bool, msg: str) -> None:
        self.pruebas += 1
        if not ok:
            self.fallos.append(msg)


def nueva_pagina(
    browser: Browser,
    size: tuple[int, int],
    modo: str,
    extra_storage: dict[str, str] | None = None,
) -> tuple[BrowserContext, Page, list[str]]:
    ctx = new_context(browser, viewport={"width": size[0], "height": size[1]})
    storage = {"qiskit:theme": modo, **(extra_storage or {})}
    ctx.add_init_script(
        f"for (const [k, v] of Object.entries({json.dumps(storage)})) localStorage.setItem(k, v);"
    )
    pg = ctx.new_page()
    errores: list[str] = []
    pg.on("pageerror", lambda e: errores.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errores.append(f"console: {m.text}") if m.type == "error" else None)
    return ctx, pg, errores


def fuera_del_stage(pg: Page) -> Any:
    return pg.evaluate(
        """() => {
          const s = document.querySelector('#stage').getBoundingClientRect();
          return [...document.querySelectorAll('#scene > .blk')].filter(b => {
            const r = b.getBoundingClientRect();
            return r.width && (r.left < s.left - 1 || r.top < s.top - 1 || r.right > s.right + 1 || r.bottom > s.bottom + 1);
          }).map(b => b.className);
        }"""
    )


def visitar(
    rep: Report, browser: Browser, base: str, shots: str | None, ultimos: dict[str, int]
) -> None:
    marcas: dict[tuple[str, str, bool], Any] = {}
    catalogos: dict[tuple[str, str], Any] = {}
    for modo in MODOS:
        for tam, size in TAMANOS.items():
            etiqueta = f"{modo}/{tam}"
            paginas = [("catalogo", f"{base}/"), ("index", f"{base}/qiskit/index.html")]
            for lid in LECCIONES:
                paginas += [
                    (f"{lid}-b0", f"{base}/qiskit/lesson.html?l={lid}&beat=0"),
                    (f"{lid}-bN", f"{base}/qiskit/lesson.html?l={lid}&beat={ultimos[lid]}"),
                ]
            for nombre, url in paginas:
                ctx, pg, errores = nueva_pagina(browser, size, modo)
                pg.goto(url)
                pg.wait_for_selector("[data-theme-ctl] button")
                pg.wait_for_timeout(1500 if nombre == "index" else 900)
                rep.check(not errores, f"{etiqueta} {nombre}: {errores}")
                attr = pg.evaluate("document.documentElement.dataset.theme")
                rep.check(attr == modo, f"{etiqueta} {nombre}: data-theme {attr}")
                if nombre not in ("index", "catalogo"):
                    fuera = fuera_del_stage(pg)
                    rep.check(not fuera, f"{etiqueta} {nombre}: blocks outside #stage {fuera}")
                marca = pg.evaluate(
                    "[document.querySelector('.brand').textContent.trim(), getComputedStyle(document.querySelector('.brand')).fontFamily,"
                    " getComputedStyle(document.body).fontFamily]"
                )
                if nombre == "catalogo":
                    catalogos[(modo, tam)] = marca
                else:
                    marcas.setdefault((modo, tam, nombre.startswith("index")), marca)
                if shots:
                    d = Path(shots) / modo
                    d.mkdir(parents=True, exist_ok=True)
                    pg.screenshot(path=str(d / f"{tam}-{nombre}.png"))
                ctx.close()
    for (modo, tam), valor in catalogos.items():
        curso = marcas[(modo, tam, True)]
        rep.check(valor[0] == "Duo", f"catalog brand {valor[0]!r}")
        rep.check(
            valor[1:] == curso[1:],
            f"the catalog fonts differ from the course fonts: {valor[1:]} / {curso[1:]}",
        )
    for (modo, tam, es_index), valor in marcas.items():
        otro = marcas[(modo, tam, not es_index)]
        rep.check(valor[0] == "Qubit a qubit", f"brand {valor[0]!r}")
        rep.check(
            valor[1] == otro[1],
            f"the brand font differs between pages: {valor[1]} / {otro[1]}",
        )


def contrastes(rep: Report, browser: Browser, base: str) -> dict[tuple[str, str], float]:
    tabla: dict[tuple[str, str], float] = {}
    for modo in MODOS:
        ctx, pg, _ = nueva_pagina(browser, (1366, 768), modo)
        pg.goto(f"{base}/qiskit/index.html")
        pg.wait_for_selector("[data-theme-ctl] button")
        nombres = set(TEXTO + SUPERFICIES + GRAFICOS + ["acc-ink", "acc"])
        col = {k: parse_color(v) for k, v in pg.evaluate(RESOLVER, sorted(nombres)).items()}
        ctx.close()
        for t in TEXTO:
            peor = min(contraste(col[t], col[s]) for s in SUPERFICIES)
            tabla[(t, modo)] = peor
            rep.check(peor >= 4.5, f"contrast {t} in {modo}: {peor:.2f} < 4.5")
        for g in GRAFICOS:
            peor = min(contraste(col[g], col[s]) for s in SUPERFICIES)
            tabla[(g, modo)] = peor
            rep.check(peor >= 3, f"contrast {g} in {modo}: {peor:.2f} < 3")
        r = contraste(col["acc-ink"], col["acc"])
        tabla[("acc-ink/acc", modo)] = r
        rep.check(r >= 4.5, f"contrast acc-ink on acc in {modo}: {r:.2f} < 4.5")
    return tabla


def imprimir_tabla(tabla: dict[tuple[str, str], float]) -> None:
    filas = [*TEXTO, "acc-ink/acc", *GRAFICOS]
    print("| token | " + " | ".join(MODOS) + " |")
    print("| --- | " + " | ".join("---:" for _ in MODOS) + " |")
    for f in filas:
        print(f"| `{f}` | " + " | ".join(f"{tabla[(f, m)]:.2f}" for m in MODOS) + " |")


def modo_guardado_una_vez(rep: Report, browser: Browser, base: str) -> None:
    ctx = new_context(browser, viewport={"width": 1366, "height": 768}, color_scheme="light")
    pg = ctx.new_page()
    pg.goto(f"{base}/qiskit/index.html")
    pg.wait_for_selector("[data-theme-ctl] button")
    rep.check(
        pg.evaluate("document.documentElement.dataset.theme") is None,
        "with no stored mode the page sets data-theme instead of following the system",
    )
    fondo = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    pg.click("[data-theme-ctl] button")
    rep.check(
        pg.evaluate("localStorage.getItem('qiskit:theme')") == "dark",
        "the mode button did not store the dark mode",
    )
    rep.check(
        pg.evaluate("getComputedStyle(document.body).backgroundColor") != fondo,
        "the background did not change with the mode",
    )
    pg.goto(f"{base}/qiskit/lesson.html?l=p1-quickstart&beat=0")
    pg.wait_for_selector("[data-theme-ctl] button")
    rep.check(
        pg.evaluate("document.documentElement.dataset.theme") == "dark",
        "the player did not read the stored mode",
    )
    rep.check(
        pg.inner_text("[data-theme-ctl] button") == "Tema claro",
        "the player button does not offer the other mode",
    )
    pg.click("[data-theme-ctl] button")
    pg.goto(f"{base}/qiskit/index.html")
    pg.wait_for_selector("[data-theme-ctl] button")
    rep.check(
        pg.evaluate("document.documentElement.dataset.theme") == "light",
        "the front page did not read the mode chosen in the player",
    )
    ctx.close()


def repaso_en_paralelo(rep: Report, browser: Browser, base: str) -> float:
    hechas = json.dumps(
        ["p1-quickstart", "p1-instalar", "p1-composer", "p1-patrones", "p3-target", "p6-panorama"]
    )
    ctx, pg, errores = nueva_pagina(browser, (1366, 768), "dark", {"qiskit:done": hechas})
    t0 = time.time()
    pg.goto(f"{base}/qiskit/index.html")
    pg.wait_for_selector("#repaso .rq", timeout=15000)
    dt = time.time() - t0
    n = len(json.loads(hechas))
    rep.check(
        dt < DEMORA_LESSON_JSON * (n - 1),
        f"the review took {dt:.2f} s with {n} lessons of {DEMORA_LESSON_JSON} s: it requests in series",
    )
    rep.check(not errores, f"review: {errores}")
    ctx.close()
    return dt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots")
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args()
    srv, base = serve()
    ultimos = {
        lid: len(
            json.loads((SITE / "qiskit" / "lessons" / lid / "lesson.json").read_text())["beats"]
        )
        - 1
        for lid in LECCIONES
    }
    rep = Report()
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        tabla = contrastes(rep, browser, base)
        modo_guardado_una_vez(rep, browser, base)
        dt = repaso_en_paralelo(rep, browser, base)
        visitar(rep, browser, base, args.shots, ultimos)
        browser.close()
    srv.shutdown()
    verify()
    if args.table:
        imprimir_tabla(tabla)
    print(f"review with 6 lessons of {DEMORA_LESSON_JSON} s each: {dt:.2f} s")
    print(f"{rep.pruebas} checks, {len(rep.fallos)} failures")
    for f in rep.fallos:
        print("FAIL", f)
    sys.exit(1 if rep.fallos else 0)


if __name__ == "__main__":
    main()
