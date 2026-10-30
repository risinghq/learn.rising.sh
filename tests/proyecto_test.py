"""Check the "Proyecto Ising" panel with Playwright and a server for site/.

    uv run --group tools python tests/proyecto_test.py

For each milestone n, store the earlier milestones as done in `qiskit:hitos` and
load the course page. The command shown matches the notebook that
`missions[].notebook` links in course.json. The track marks the same milestones
as open, and the console must log no errors.
"""

import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from offline import new_context, verify
from playwright.sync_api import Page, sync_playwright

SITE = Path(__file__).resolve().parent.parent / "site"
HITOS = 10


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def serve() -> tuple[ThreadingHTTPServer, str]:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(SITE)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def vigilar(pg: Page, errores: list[str]) -> None:
    """Append page errors and console errors to `errores`."""
    pg.on("pageerror", lambda e: errores.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errores.append(f"console: {m.text}") if m.type == "error" else None)


def cuadernos_enlazados() -> set[str]:
    curso = json.loads((SITE / "qiskit" / "course.json").read_text())
    return {
        m["notebook"]
        for parte in curso["parts"]
        for leccion in parte["lessons"]
        for m in leccion.get("missions", [])
    }


def main() -> None:
    enlazados = cuadernos_enlazados()
    abiertos = [n for n in range(1, HITOS + 1) if f"practica/proyecto/hito{n}.py" in enlazados]
    fallos: list[str] = []
    srv, base = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for n in range(1, HITOS + 1):
            nb = f"practica/proyecto/hito{n}.py"
            esperado = nb in enlazados
            ctx = new_context(browser, viewport={"width": 1366, "height": 768})
            ctx.add_init_script(
                f"localStorage.setItem('qiskit:hitos', {json.dumps(json.dumps(list(range(1, n))))});"
            )
            pg = ctx.new_page()
            errores: list[str] = []
            vigilar(pg, errores)
            pg.goto(f"{base}/qiskit/")
            # The page paints what the server rendered first, then what the browser stored.
            pg.wait_for_function(
                "n => document.querySelector('.hcur p')?.textContent?.startsWith(`Hito ${n} de`)",
                arg=n,
            )
            comandos = pg.locator(".hcur .cmd code").all_text_contents()
            esperados = [f"uv run marimo edit {nb}"] if esperado else []
            if comandos != esperados:
                fallos.append(f"hito {n}: command {comandos}, expected {esperados}")
            estados = pg.locator(".track .hito").evaluate_all(
                "els => els.map(e => e.dataset.state)"
            )
            previstos = [
                "done"
                if k < n
                else "current"
                if k == n
                else "open"
                if f"practica/proyecto/hito{k}.py" in enlazados
                else "locked"
                for k in range(1, HITOS + 1)
            ]
            if estados != previstos:
                fallos.append(f"hito {n}: track {estados}, expected {previstos}")
            if errores:
                fallos.append(f"hito {n}: {errores}")
            ctx.close()
        browser.close()
    srv.shutdown()
    verify()
    print(f"milestones open according to course.json: {abiertos}")
    print(f"{HITOS} milestones checked, {len(fallos)} failures")
    for f in fallos:
        print("FAIL", f)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
