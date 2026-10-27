"""Comprueba en el navegador el editor de los ejercicios con Playwright y tools/serve.py.

    uv run --group tools python tests/exercise_ui_test.py [--shots CARPETA]

Abre el paso de misión de cada lección con ejercicios, prueba el editor en escritorio y móvil,
y comprueba que el progreso se conserva. También prueba el teclado, el tema, los estados de carga
y error, y la comprobación de Turnstile. `--shots` guarda capturas.
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from unittest import mock

from playwright.sync_api import Browser, Locator, Page, Route, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from offline import new_context, verify  # noqa: E402

from qgcheck import spec  # noqa: E402

DESKTOP: dict[str, Any] = {"viewport": {"width": 1280, "height": 900}}
MOBILE: dict[str, Any] = {
    "viewport": {"width": 390, "height": 844},
    "is_mobile": True,
    "has_touch": True,
    "device_scale_factor": 2,
}

GHZ_WITHOUT_CHAIN = """from qiskit import QuantumCircuit


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc
"""
GHZ_CAPPED_AT_FOUR = """from qiskit import QuantumCircuit


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(min(n - 1, 3)):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc
"""
BELL_WITH_Z = """from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

anti = QuantumCircuit(2)
anti.h(0)
anti.cx(0, 1)
anti.z(1)
anti.measure_all()

resultado = StatevectorSampler(seed=7).run([anti], shots=1024).result()
print(resultado[0].data.meas.get_counts())
"""
# (lección, posición del ejercicio en el paso, ejercicio, código equivocado o None para el inicial, caso que falla)
EXERCISES: list[tuple[str, int, str, str | None, str]] = [
    ("p1-quickstart", 1, "ghz", GHZ_WITHOUT_CHAIN, "n = 2, 3 y 4"),
    ("p1-quickstart", 0, "bell-distinto", BELL_WITH_Z, "Salen ['00', '11']"),
    ("p2-control-clasico", 1, "siempre-uno", None, "el resultado final es siempre 1"),
    ("p2-circuitos", 0, "profundidad", None, "tu apuesta es la profundidad de qc"),
    ("p2-visualizar", 2, "barras-esperados", None, "Bell: ⟨ZZ⟩ = ⟨XX⟩ = 1"),
]

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
    print("✓" if ok else "✗", msg)


def serve(handler: type[SimpleHTTPRequestHandler]) -> str:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def quiet(base: type[SimpleHTTPRequestHandler]) -> type[SimpleHTTPRequestHandler]:
    return type("Quiet", (base,), {"log_message": lambda *a: None})


def mission_url(lesson: str) -> str:
    beats = json.loads(
        (ROOT / "site" / "qiskit" / "lessons" / lesson / "lesson.json").read_text(encoding="utf-8")
    )["beats"]
    return f"/qiskit/lesson.html?l={lesson}&beat={next(i for i, b in enumerate(beats) if b['id'] == 'mision')}"


def read(lesson: str, name: str, part: str) -> str:
    return (ROOT / "exercises" / lesson / name / part).read_text(encoding="utf-8").rstrip("\n")


def open_panel(page: Page, base: str, lesson: str, k: int) -> Locator:
    page.goto(base + mission_url(lesson))
    panel = page.locator(".xpanel").nth(k)
    panel.locator(".cm-editor").wait_for()
    return panel


def write(page: Page, panel: Locator, code: str) -> None:
    panel.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)


def editor_text(panel: Locator) -> str:
    """El texto del editor sin líneas en blanco: inner_text las cuenta distinto según el diseño."""
    return "\n".join(
        line.rstrip()
        for line in panel.locator(".cm-content").inner_text().split("\n")
        if line.strip()
    )


def unblank(code: str) -> str:
    return "\n".join(line.rstrip() for line in code.split("\n") if line.strip())


def press(panel: Locator, name: str) -> None:
    panel.get_by_role("button", name=name).click()


def wait_result(panel: Locator, timeout: int = 40_000) -> None:
    panel.locator(".xstatus.ok, .xstatus.bad").wait_for(timeout=timeout)


def shot(page: Page, shots: str | None, name: str, panel: Locator, results: bool = False) -> None:
    """En pantallas estrechas el resultado queda bajo el editor: se encuadra el resultado."""
    if shots:
        viewport = page.viewport_size
        assert viewport is not None
        narrow = viewport["width"] < 640
        target = panel.locator(".xstatus") if results and narrow else panel
        target.evaluate("e => e.scrollIntoView({block: 'start'})")
        page.screenshot(path=str(Path(shots) / f"{name}.png"))


def flow(
    browser: Browser,
    base: str,
    label: str,
    ctx: dict[str, Any],
    lesson: str,
    k: int,
    name: str,
    wrong: str | None,
    failing_case: str,
    shots: str | None,
) -> None:
    """Equivocado, falla un caso; corregido, pasa; tras recargar, el progreso sigue."""
    solution = read(lesson, name, "solution.py")
    page = new_context(browser, **ctx).new_page()
    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    panel = open_panel(page, base, lesson, k)
    tag = f"{label} {lesson}/{name}"
    if wrong:
        write(page, panel, wrong)
    shot(page, shots, f"{label}-{name}-escrito", panel)
    press(panel, "Comprobar")
    wait_result(panel)
    check(
        panel.locator(".xstatus.bad").count() == 1 and panel.locator(".xtests li.bad").count() >= 1,
        f"{tag}: el código equivocado falla un caso",
    )
    check(
        failing_case in panel.locator(".xtests li.bad").first.inner_text(),
        f"{tag}: el caso que falla trae su nombre o su mensaje ({failing_case})",
    )
    check(panel.locator(".xsolved").is_hidden(), f"{tag}: aún no figura como resuelto")
    shot(page, shots, f"{label}-{name}-falla", panel, results=True)
    write(page, panel, solution)
    press(panel, "Comprobar")
    wait_result(panel)
    check(
        "¡Pasa todos los casos!" in panel.locator(".xstatus").inner_text(),
        f"{tag}: la solución pasa todos los casos",
    )
    check(
        panel.locator(".xtests li.bad").count() == 0 and panel.locator(".xsolved").is_visible(),
        f"{tag}: figura como resuelto",
    )
    shot(page, shots, f"{label}-{name}-pasa", panel, results=True)
    page.reload()
    panel = page.locator(".xpanel").nth(k)
    panel.locator(".cm-editor").wait_for()
    check(editor_text(panel) == unblank(solution), f"{tag}: tras recargar, el código sigue")
    check(panel.locator(".xsolved").is_visible(), f"{tag}: tras recargar, sigue resuelto")
    check(not errors, f"{tag}: sin errores en consola {errors}")
    page.context.close()


def feedback(browser: Browser, base: str, shots: str | None) -> None:
    cases = spec.load_cases(spec.folder("p1-quickstart/ghz") / "check.py")
    page = new_context(browser, **DESKTOP).new_page()
    panel = open_panel(page, base, "p1-quickstart", 1)

    write(
        page,
        panel,
        "from qiskit import QuantumCircuit\n\n\ndef ghz(n:\n    return QuantumCircuit(n)\n",
    )
    press(panel, "Comprobar")
    wait_result(panel)
    error = panel.locator(".xerr").inner_text()
    check(
        "SyntaxError" in error and "línea 4" in error,
        f"error de sintaxis: el panel muestra el error con su línea ({error})",
    )
    check(
        "No se pudo probar tu código" in panel.locator(".xout").inner_text(),
        "error de sintaxis: el panel dice que no se pudo probar el código",
    )
    check(
        panel.locator(".xtests").count() == 0 and panel.locator(".xtests li").count() == 0,
        "error de sintaxis: no se muestra ningún caso",
    )
    check(
        "Pasan" not in panel.locator(".xstatus").inner_text(),
        "error de sintaxis: no se cuentan casos",
    )
    shot(page, shots, "escritorio-ghz-sintaxis", panel, results=True)

    visible = sum(shown is not None for _, shown in cases)
    hidden = len(cases) - visible
    write(page, panel, GHZ_CAPPED_AT_FOUR)
    press(panel, "Comprobar")
    wait_result(panel)
    status = panel.locator(".xstatus").inner_text()
    check(
        f"{visible} de {visible} visibles · 0 de {hidden} ocultos" in status,
        f"casos ocultos: se cuentan aparte de los visibles ({status})",
    )
    failing = panel.locator(".xtests li.bad")
    check(
        failing.count() == hidden and all("caso oculto" in t for t in failing.all_inner_texts()),
        "casos ocultos: solo fallan los ocultos",
    )
    shot(page, shots, "escritorio-ghz-oculto", panel, results=True)
    page.context.close()

    # El servidor lee el check.py de prueba desde QG_EXERCISES.
    with tempfile.TemporaryDirectory(prefix="qg-ui-") as scratch, mock.patch.dict(os.environ):
        # Las fuentes pueden ser de solo lectura; la copia se edita y se borra, así que se deja escribible.
        copy = Path(scratch) / "exercises"
        shutil.copytree(ROOT / "exercises", copy, copy_function=shutil.copyfile)
        for path in [copy, *copy.rglob("*")]:
            path.chmod(0o755 if path.is_dir() else 0o644)
        check_file = copy / "p1-quickstart" / "ghz" / "check.py"
        source = check_file.read_text(encoding="utf-8")
        check_file.write_text(
            source.replace(
                '@visible("n = 2, 3 y 4")', '@visible("n = 2, 3 y 4")\n@hint(1)'
            ).replace("from qgcheck import ", "from qgcheck import hint, ", 1),
            encoding="utf-8",
        )
        lesson = json.loads(
            (ROOT / "site" / "qiskit" / "lessons" / "p1-quickstart" / "lesson.json").read_text(
                encoding="utf-8"
            )
        )
        tip = next(
            blk["hints"][0]
            for b in lesson["beats"]
            for blk in b["scene"]
            if blk.get("exercise") == "p1-quickstart/ghz"
        )
        os.environ["QG_EXERCISES"] = str(copy)
        page = new_context(browser, **DESKTOP).new_page()
        panel = open_panel(page, base, "p1-quickstart", 1)
        write(page, panel, GHZ_WITHOUT_CHAIN)
        press(panel, "Comprobar")
        wait_result(panel)
        named = panel.locator(".xtests li.bad", has_text="n = 2, 3 y 4")
        check(
            named.locator(".xcasehint").count() == 1
            and tip.replace("`", "") in named.locator(".xcasehint").inner_text(),
            "pista del caso: el caso que falla muestra la pista que nombra",
        )
        check(
            panel.locator(".xtests li.bad").locator(".xcasehint").count() == 1,
            "pista del caso: los casos que no nombran pista no la muestran",
        )
        check(
            panel.locator(".xhint:not(.xcasehint)").count() == 0,
            "pista del caso: no cuenta como pista pedida con el botón",
        )
        page.context.close()


def height(button: Locator) -> float:
    box = button.bounding_box()
    assert box is not None
    return box["height"]


def mobile_layout(browser: Browser, base: str, shots: str | None) -> None:
    page = new_context(browser, **MOBILE).new_page()
    panel = open_panel(page, base, "p1-quickstart", 1)
    panel.scroll_into_view_if_needed()
    box = panel.bounding_box()
    assert box is not None
    check(
        page.evaluate("document.documentElement.scrollWidth") <= 390,
        "móvil: la página no se desplaza en horizontal",
    )
    check(
        box["x"] >= 0 and box["x"] + box["width"] <= 390,
        "móvil: el panel cabe en el ancho de la pantalla",
    )
    check(
        page.evaluate("getComputedStyle(document.querySelector('#stage')).transform") == "none",
        "móvil: el paso con ejercicio no se escala",
    )
    sizes = [height(panel.get_by_role("button", name=n)) for n in ("Ejecutar", "Comprobar")]
    check(min(sizes) >= 40, f"móvil: los botones se pulsan con el dedo ({sizes})")
    check(
        panel.locator(".cm-content").evaluate("e => parseFloat(getComputedStyle(e).fontSize)")
        >= 16,
        "móvil: el código se lee a 16 px o más",
    )
    shot(page, shots, "movil-ghz-inicio", panel)
    page.context.close()


def keyboard(browser: Browser, base: str) -> None:
    page = new_context(browser, **DESKTOP).new_page()
    panel = open_panel(page, base, "p1-quickstart", 1)
    editor = panel.locator(".cm-content")
    write(page, panel, "x")
    page.keyboard.type(" c")
    check(
        editor_text(panel) == "x c" and page.locator('#cc[aria-pressed="true"]').count() == 1,
        "teclado: escribir espacio y «c» en el editor no activa los atajos de la lección",
    )
    page.keyboard.press("ArrowLeft")
    check(panel.is_visible(), "teclado: las flechas del editor no cambian de paso")
    write(page, panel, "x")
    page.keyboard.press("Home")
    page.keyboard.press("Tab")
    check(editor_text(panel) == "    x", "teclado: Tab sangra cuatro espacios")
    page.keyboard.press("Escape")
    page.keyboard.press("Tab")
    check(
        page.evaluate("!document.activeElement.closest('.cm-editor')"),
        "teclado: Esc y Tab sacan el foco del editor",
    )
    write(page, panel, 'print("hola")')
    editor.press("ControlOrMeta+Enter")
    panel.locator(".xstdout").wait_for(timeout=40_000)
    check(
        "hola" in panel.locator(".xstdout").inner_text()
        and "ejecutó sin errores" in panel.locator(".xstatus").inner_text(),
        "teclado: Ctrl+Intro ejecuta y muestra la salida",
    )
    check(panel.locator(".xtests").count() == 0, "teclado: Ejecutar no corre los casos")
    write(page, panel, "print(1)\nprint(y)")
    editor.press("ControlOrMeta+Shift+Enter")
    wait_result(panel)
    check(
        "línea 2" in panel.locator(".xerr").inner_text()
        and "tiene un error" in panel.locator(".xstatus").inner_text(),
        "teclado: Ctrl+Mayús+Intro comprueba y muestra el error con su línea",
    )
    check(
        panel.locator(".cm-errline").count() == 1
        and "print(y)" in panel.locator(".cm-errline").inner_text(),
        "el editor marca la línea del error",
    )
    write(page, panel, "print(1)\nprint(y)\n")
    check(panel.locator(".cm-errline").count() == 0, "la marca del error se quita al editar")
    page.context.close()


def hints(browser: Browser, base: str) -> None:
    page = new_context(browser, **DESKTOP).new_page()
    panel = open_panel(page, base, "p1-quickstart", 1)
    lesson = json.loads(
        (ROOT / "site" / "qiskit" / "lessons" / "p1-quickstart" / "lesson.json").read_text(
            encoding="utf-8"
        )
    )
    total = next(
        len(blk["hints"])
        for b in lesson["beats"]
        for blk in b["scene"]
        if blk.get("exercise") == "p1-quickstart/ghz"
    )
    check(panel.locator(".xhint").count() == 0, "pistas: al abrir no hay ninguna")
    press(panel, "Pista")
    press(panel, "Pista")
    check(panel.locator(".xhint").count() == 2, "pistas: una más por pulsación")
    page.reload()
    panel = page.locator(".xpanel").nth(1)
    panel.locator(".cm-editor").wait_for()
    check(panel.locator(".xhint").count() == 2, "pistas: las vistas se conservan al recargar")
    press(panel, f"Pista (2/{total})")
    check(
        panel.locator(".xhint").count() == total
        and panel.get_by_role("button", name="Sin más pistas").is_disabled(),
        "pistas: la última deja el botón sin uso",
    )
    page.context.close()


def theme(browser: Browser, base: str) -> None:
    page = new_context(browser, **DESKTOP).new_page()
    paint = "e => getComputedStyle(e).backgroundColor"
    probe = """() => { const d = document.createElement('div'); d.style.background = 'var(--code-bg)'; document.body.append(d);
                 const c = getComputedStyle(d).backgroundColor; d.remove(); return c; }"""
    seen: dict[str, str] = {}
    for mode in ("light", "dark"):
        page.add_init_script(f"localStorage.setItem('qiskit:theme', '{mode}')")
        panel = open_panel(page, base, "p1-quickstart", 1)
        seen[mode] = panel.locator(".cm-editor").evaluate(paint)
        check(
            seen[mode] == page.evaluate(probe),
            f"tema {mode}: el editor usa --code-bg ({seen[mode]})",
        )
    check(seen["light"] != seen["dark"], "tema: el editor cambia con el modo claro y oscuro")
    page.context.close()


def states(browser: Browser, base: str) -> None:
    """Cargando, tiempo agotado del código, y errores del corredor."""
    page = new_context(browser, **DESKTOP).new_page()
    panel = open_panel(page, base, "p1-quickstart", 1)
    write(page, panel, "while True:\n    pass")
    press(panel, "Ejecutar")
    check(
        panel.locator(".xstatus.busy").is_visible()
        and panel.get_by_role("button", name="Ejecutar").is_disabled()
        and panel.get_by_role("button", name="Comprobar").is_disabled(),
        "carga: mientras corre se ve «Ejecutando…» y los botones se bloquean",
    )
    wait_result(panel)
    check(
        "más de 10 s" in panel.locator(".xerr").inner_text()
        and panel.get_by_role("button", name="Ejecutar").is_enabled(),
        "tiempo agotado: el código infinito se corta con su mensaje y los botones vuelven",
    )

    page.route(
        "**/run",
        lambda r: r.fulfill(
            status=503, content_type="application/json", body='{"error": "ocupado"}'
        ),
    )
    press(panel, "Ejecutar")
    panel.locator(".xstatus.bad").wait_for()
    check(
        "ocupado" in panel.locator(".xstatus").inner_text(),
        "error: un 503 dice que el corredor está ocupado",
    )
    page.unroute("**/run")
    page.route("**/run", lambda r: r.abort())
    press(panel, "Ejecutar")
    panel.locator(".xstatus", has_text="No se pudo conectar").wait_for()
    check(
        panel.get_by_role("button", name="Ejecutar").is_enabled(),
        "error: sin conexión se dice y se puede reintentar",
    )
    page.context.close()

    page = new_context(browser, **DESKTOP).new_page()
    page.clock.install()
    panel = open_panel(page, base, "p1-quickstart", 1)
    held: list[Route] = []
    page.route(
        "**/run", lambda r: held.append(r)
    )  # Mantiene la petición abierta para probar el tiempo límite.
    press(panel, "Comprobar")
    page.clock.run_for(5_000)
    check(
        "Esperando al corredor" in panel.locator(".xstatus").inner_text(),
        "carga: tras unos segundos explica que el corredor puede tardar",
    )
    page.clock.run_for(30_000)
    panel.locator(".xstatus", has_text="no respondió").wait_for()
    check(
        panel.get_by_role("button", name="Comprobar").is_enabled(),
        "tiempo agotado: si el corredor no responde se corta y se puede reintentar",
    )
    for route in held:
        route.abort()
    page.context.close()


# Sustituye el widget de Turnstile y entrega un token de prueba.
FAKE_TURNSTILE = """window.turnstile = {
  render(slot, o) { slot.dataset.sitekey = o.sitekey; setTimeout(() => o.callback('XXXX.DUMMY.TOKEN.XXXX'), 20); return 'w1'; },
  remove() { window.turnstileRemoved = (window.turnstileRemoved || 0) + 1; },
};"""


def turnstile(browser: Browser, base: str) -> None:
    """Comprueba la petición inicial de Turnstile y la sesión que deja abierta."""
    page = new_context(browser, **DESKTOP).new_page()
    sent: list[str | None] = []
    scripts: list[str] = []
    session: list[str] = []
    refusal = {
        "error": "Antes de ejecutar código hay que comprobar que eres una persona.",
        "reason": "turnstile_missing",
        "sitekey": "1x00000000000000000000AA",
    }

    def run(route: Route) -> None:
        token = route.request.headers.get("x-turnstile-token")
        sent.append(token)
        if token:
            session.append(token)
        if token or session:
            route.continue_()
            return
        route.fulfill(status=403, content_type="application/json", body=json.dumps(refusal))

    def widget(route: Route) -> None:
        scripts.append(route.request.url)
        route.fulfill(content_type="text/javascript", body=FAKE_TURNSTILE)

    page.route("**/run", run)
    page.route("https://challenges.cloudflare.com/turnstile/v0/api.js*", widget)
    panel = open_panel(page, base, "p1-quickstart", 1)
    write(page, panel, "print(1)")
    press(panel, "Ejecutar")
    wait_result(panel)
    check(
        sent == [None, "XXXX.DUMMY.TOKEN.XXXX"]
        and "Se ejecutó sin errores" in panel.locator(".xstatus").inner_text(),
        f"turnstile: la primera ejecución repite la petición con el token ({sent})",
    )
    check(
        len(scripts) == 1
        and page.evaluate("window.turnstileRemoved") == 1
        and page.locator(".xturnstile").count() == 0,
        "turnstile: el widget se carga una vez y se retira al terminar",
    )
    press(panel, "Ejecutar")
    wait_result(panel)
    check(
        sent == [None, "XXXX.DUMMY.TOKEN.XXXX", None] and len(scripts) == 1,
        f"turnstile: con la sesión abierta no se vuelve a pedir ({sent})",
    )

    page.context.close()

    page = new_context(browser, **DESKTOP).new_page()
    page.route(
        "**/run",
        lambda r: r.fulfill(status=403, content_type="application/json", body=json.dumps(refusal)),
    )
    page.route("https://challenges.cloudflare.com/turnstile/v0/api.js*", lambda r: r.abort())
    panel = open_panel(page, base, "p1-quickstart", 1)
    press(panel, "Ejecutar")
    panel.locator(".xstatus", has_text="comprobación de que eres una persona").wait_for()
    check(
        panel.get_by_role("button", name="Ejecutar").is_enabled(),
        "turnstile: si el widget no carga se dice y se puede reintentar",
    )
    page.context.close()


def main() -> None:
    shots = None
    if "--shots" in sys.argv:
        shots = sys.argv[sys.argv.index("--shots") + 1]
        Path(shots).mkdir(parents=True, exist_ok=True)
    tool_spec = importlib.util.spec_from_file_location("serve_tool", ROOT / "tools" / "serve.py")
    assert tool_spec is not None and tool_spec.loader is not None
    tool = importlib.util.module_from_spec(tool_spec)
    tool_spec.loader.exec_module(tool)
    base = serve(quiet(tool.Handler))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for label, ctx in (("escritorio", DESKTOP), ("movil", MOBILE)):
            for lesson, k, name, wrong, case in (
                EXERCISES if label == "escritorio" else EXERCISES[:1]
            ):
                flow(browser, base, label, ctx, lesson, k, name, wrong, case, shots)
        feedback(browser, base, shots)
        mobile_layout(browser, base, shots)
        keyboard(browser, base)
        hints(browser, base)
        theme(browser, base)
        states(browser, base)
        turnstile(browser, base)
        browser.close()
    verify()
    print(f"\n{len(failures)} fallos" if failures else "\ntodo bien")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
