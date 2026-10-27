"""Comprueba la cuenta opcional en un navegador con un Worker local y un proveedor falso.

    uv run --group tools python tests/account_ui_test.py

Comprueba la sincronización entre dos navegadores y que borrar la cuenta conserva
la copia local. Sin cuenta, la página solo hace la petición propia de `/run`.
Se omite con el motivo si faltan Node o las dependencias del Worker.
"""

import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Page, Route, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exercise_ui_test import (
    DESKTOP,
    FAKE_TURNSTILE,
    ROOT,
    editor_text,
    open_panel,
    press,
    unblank,
    wait_result,
    write,
)
from offline import new_context, verify

WORKER = ROOT / "runner" / "worker"
LESSON = "p1-quickstart"
EXERCISE = "p1-quickstart/ghz"
# El corredor falso da por fallida una comprobación cuyo código contiene FALLA.
FAILING = "# FALLA\nprint('primer intento')\n"
REWRITTEN = "# FALLA\nprint('desde el otro navegador')\n"
SUBJECT = "424242"

failures: list[str] = []

Requests = list[tuple[str, str]]
Tab = tuple[Page, list[str], Requests]


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
    print("✓" if ok else "✗", msg)


def call(url: str, body: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(
        url,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def start_worker() -> tuple[subprocess.Popen[str], dict[str, str]]:
    process = subprocess.Popen(
        ["node", "test/serve.ts"],
        cwd=WORKER,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None and process.stderr is not None
    line = process.stdout.readline()
    if not line:
        process.kill()
        raise RuntimeError(f"el Worker local no arrancó: {process.stderr.read()}")
    return process, json.loads(line)


def last_beat(lesson: str) -> int:
    beats = json.loads(
        (ROOT / "site" / "qiskit" / "lessons" / lesson / "lesson.json").read_text(encoding="utf-8")
    )["beats"]
    return len(beats) - 1


def new_page(browser: Browser, site: str, control: str) -> Tab:
    """Un navegador nuevo: el widget de Turnstile y la pantalla del proveedor son falsos."""
    context = new_context(browser, **DESKTOP)
    context.route(
        "https://challenges.cloudflare.com/turnstile/v0/api.js*",
        lambda r: r.fulfill(content_type="text/javascript", body=FAKE_TURNSTILE),
    )

    def provider(route: Route) -> None:
        """El Worker redirige al proveedor. El navegador no sigue esa redirección a través de route, así que se
        responde aquí por el proveedor: el alumno aprueba y vuelve a la dirección de retorno con el código."""
        response = route.fetch(max_redirects=0)
        authorize = response.headers["location"]
        code = call(f"{control}/consent", {"authorizeUrl": authorize, "subject": SUBJECT})["code"]
        query = urllib.parse.parse_qs(urllib.parse.urlparse(authorize).query)
        back = urllib.parse.urlencode({"code": code, "state": query["state"][0]})
        route.fulfill(
            response=response,
            headers={**response.headers, "location": f"{query['redirect_uri'][0]}?{back}"},
        )

    context.route(re.compile(r"/auth/github\?"), provider)
    page = context.new_page()
    errors: list[str] = []
    requests: Requests = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on(
        "request",
        lambda r: (
            requests.append((r.method, r.url.removeprefix(site)))
            if r.url.startswith(site)
            else None
        ),
    )
    return page, errors, requests


def stored(page: Page, key: str) -> Any:
    return json.loads(page.evaluate("key => localStorage.getItem(key)", key) or "null")


def menu(page: Page, name: str) -> None:
    page.get_by_role("button", name=name, exact=True).click()


def sign_in(page: Page) -> None:
    menu(page, "Entrar")
    page.get_by_role("button", name="Entrar con GitHub", exact=True).click()
    page.get_by_role("button", name="Cuenta ✓", exact=True).wait_for()


def anonymous(browser: Browser, site: str, control: str) -> Tab:
    page, errors, requests = new_page(browser, site, control)
    page.goto(f"{site}/qiskit/index.html")
    page.locator("#parts .part").first.wait_for()
    page.locator("#hito .chk").click()
    page.goto(f"{site}/qiskit/privacidad.html")
    panel = open_panel(page, site, LESSON, 1)
    write(page, panel, FAILING)
    press(panel, "Comprobar")
    wait_result(panel)
    check(panel.locator(".xstatus.bad").count() == 1, "anónimo: la comprobación falla")
    page.goto(f"{site}/qiskit/lesson.html?l={LESSON}&beat={last_beat(LESSON)}")
    page.locator("#next").click()
    page.locator("#end:not(.hide)").wait_for()
    check(
        stored(page, "qiskit:done") == [LESSON], "anónimo: la lección queda hecha en el navegador"
    )
    record = stored(page, f"qiskit:exercise:{EXERCISE}")
    check(
        record["code"] == FAILING
        and record["checks"] == 1
        and not record.get("passed")
        and record["at"] > 0,
        f"anónimo: el ejercicio guarda código, una comprobación fallida y la hora ({record})",
    )
    page.wait_for_timeout(2500)
    ours = {
        (m, p.split("?")[0].split("#")[0])
        for m, p in requests
        if p.startswith(("/api", "/auth", "/health")) or m != "GET"
    }
    check(
        ours == {("POST", "/run")},
        f"anónimo: la única petición propia que no es un archivo es /run ({sorted(ours)})",
    )
    check(stored(page, "qiskit:hitos") == [1], "anónimo: el hito marcado queda en el navegador")
    check(
        page.locator(".acct > button").first.inner_text() == "Entrar",
        "anónimo: el menú ofrece entrar",
    )
    return page, errors, requests


def main() -> None:
    if not shutil.which("node") or not (WORKER / "node_modules" / "miniflare").is_dir():
        print("se omite: hace falta node y `mise run install`")
        return
    worker, urls = start_worker()
    site, control = urls["site"], urls["control"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            one, one_errors, one_requests = anonymous(browser, site, control)
            check(
                call(f"{control}/rows")["users"] == 0,
                "anónimo: el servidor no tiene ninguna cuenta",
            )

            one.goto(f"{site}/qiskit/lesson.html?l={LESSON}&beat={last_beat(LESSON)}")
            sign_in(one)
            rows = call(f"{control}/rows")
            check(
                rows["users"] == 1
                and rows["lesson_done"] == 1
                and rows["exercise_state"] == 1
                and rows["kv"] == 1,
                f"al entrar: la cuenta guarda la lección, el ejercicio y el hito ({rows})",
            )
            check(
                stored(one, "qiskit:done") == [LESSON]
                and stored(one, f"qiskit:exercise:{EXERCISE}")["code"] == FAILING,
                "al entrar: la copia local se conserva",
            )

            two, two_errors, _ = new_page(browser, site, control)
            two.goto(f"{site}/qiskit/index.html")
            sign_in(two)
            two.locator("#parts .part").first.wait_for()
            check(
                two.locator("#prog").inner_text().startswith("1/"),
                f"otro navegador: la portada cuenta la lección como hecha ({two.locator('#prog').inner_text()})",
            )
            check(
                two.locator("#track .hito.done").count() == 1,
                "otro navegador: la portada marca el hito",
            )
            panel = open_panel(two, site, LESSON, 1)
            check(
                editor_text(panel) == unblank(FAILING),
                "otro navegador: el editor trae el código del primero",
            )
            check(
                stored(two, f"qiskit:exercise:{EXERCISE}")["checks"] == 1,
                "otro navegador: trae la comprobación fallida",
            )

            with two.expect_response(lambda r: r.url.endswith("/api/progress") and r.status == 204):
                write(two, panel, REWRITTEN)
            panel = open_panel(one, site, LESSON, 1)
            check(
                editor_text(panel) == unblank(REWRITTEN),
                "al cargar: gana el código más reciente de la cuenta",
            )

            menu(one, "Cuenta ✓")
            menu(one, "Borrar mi cuenta")
            menu(one, "Sí, borrar")
            one.get_by_role("button", name="Entrar", exact=True).wait_for()
            rows = call(f"{control}/rows")
            check(all(n == 0 for n in rows.values()), f"borrar: el servidor queda vacío ({rows})")
            check(
                stored(one, "qiskit:done") == [LESSON]
                and stored(one, f"qiskit:exercise:{EXERCISE}")["code"] == REWRITTEN,
                "borrar: la copia local se queda",
            )
            me = one.context.request.get(f"{site}/api/me").json()
            check(me == {"signedIn": False}, f"borrar: la sesión se cerró ({me})")
            before = len(one_requests)
            one.reload()
            one.locator(".xpanel").nth(1).locator(".cm-editor").wait_for()
            after = [r for r in one_requests[before:] if r[1].startswith(("/api", "/auth"))]
            check(not after, f"borrar: la página ya no habla con la cuenta ({after})")

            for errors in (one_errors, two_errors):
                check(not errors, f"sin errores de la página {errors}")
            browser.close()
    finally:
        worker.terminate()
        worker.wait(timeout=30)
    verify()
    print(f"\n{len(failures)} fallos" if failures else "\ntodo bien")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
