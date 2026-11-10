"""Check the project track and its exercise links in the course path."""

import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast

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
    pg.on("pageerror", lambda e: errores.append(f"pageerror: {e}"))
    pg.on("console", lambda m: errores.append(f"console: {m.text}") if m.type == "error" else None)


def milestones() -> list[dict[str, object]]:
    data = json.loads((SITE / "qiskit" / "project.json").read_text())
    return cast(list[dict[str, object]], data["milestones"])


def exercise_ids(lesson: str) -> set[str]:
    data = json.loads((SITE / "qiskit" / "lessons" / lesson / "lesson.json").read_text())

    def walk(blocks: list[dict[str, object]]) -> set[str]:
        found: set[str] = set()
        for block in blocks:
            if block.get("type") == "exercise":
                found.add(cast(str, block["exercise"]))
            for child in (block.get("items", []), block.get("body", [])):
                if isinstance(child, list):
                    found.update(walk([value for value in child if isinstance(value, dict)]))
        return found

    return {
        exercise
        for beat in cast(list[dict[str, object]], data["beats"])
        for exercise in walk(cast(list[dict[str, object]], beat["scene"]))
    }


def main() -> None:
    datos = milestones()
    assert len(datos) == HITOS
    for milestone in datos:
        assert cast(str, milestone["exercise"]) in exercise_ids(cast(str, milestone["lesson"]))
    fallos: list[str] = []
    srv, base = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for n in range(1, HITOS + 1):
            ctx = new_context(browser, viewport={"width": 1366, "height": 768})
            ctx.add_init_script(
                f"localStorage.setItem('qiskit:hitos', {json.dumps(json.dumps(list(range(1, n))))});"
            )
            pg = ctx.new_page()
            errores: list[str] = []
            vigilar(pg, errores)
            pg.goto(f"{base}/qiskit/")
            pg.wait_for_function(
                "n => document.querySelector('.hcur p')?.textContent?.startsWith(`Hito ${n} de`)",
                arg=n,
            )
            hrefs = pg.locator(".hcur a.btn").evaluate_all(
                "els => els.map(e => e.getAttribute('href'))"
            )
            esperado = f"/qiskit/lesson.html?l={datos[n - 1]['lesson']}"
            if hrefs != [esperado]:
                fallos.append(f"hito {n}: exercise link {hrefs}, expected {[esperado]}")
            estados = pg.locator(".track .hito").evaluate_all(
                "els => els.map(e => e.dataset.state)"
            )
            previstos = [
                "done" if k < n else "current" if k == n else "open" for k in range(1, HITOS + 1)
            ]
            if estados != previstos:
                fallos.append(f"hito {n}: track {estados}, expected {previstos}")
            if errores:
                fallos.append(f"hito {n}: {errores}")
            ctx.close()
        browser.close()
    srv.shutdown()
    verify()
    print(f"{HITOS} milestones checked, {len(fallos)} failures")
    for fallo in fallos:
        print("FAIL", fallo)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
