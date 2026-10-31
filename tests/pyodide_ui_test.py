"""Test, in a browser, the exercises that run on Pyodide and the session gate of the runner.

    uv run --group tools python tests/pyodide_ui_test.py

Física computacional: the starter fails and the solution passes with every request to /run
refused, the browser verdict equals the server's (`qgcheck.grade`), and a second visit grades
with the Pyodide files gone from the network because the service worker holds them.
Qiskit, on a host that is not local: with no session the editor shows the sign-in links in place
of the run buttons and no request reaches /run.
"""

import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, Locator, Page, Route, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import offline  # noqa: E402

from qgcheck import grade, spec  # noqa: E402

DESKTOP: dict[str, Any] = {"viewport": {"width": 1280, "height": 900}}
# A host that is not local, as in production: the gate applies there. The browser maps it to the
# test server, and the offline guard lets it through.
GATED_HOST = "rising.test"
PHYSICS = "computational-physics"
RESULT = ".xstatus.ok, .xstatus.bad"

failures: list[str] = []
served: list[str] = []
pyodide_up = threading.Event()


def check(ok: bool, msg: str) -> None:
    if not ok:
        failures.append(msg)
    print("✓" if ok else "✗", msg)


class Site(SimpleHTTPRequestHandler):
    """The static site. Once `pyodide_up` is cleared, /vendor/pyodide answers 503."""

    def do_GET(self) -> None:
        if self.path.startswith("/vendor/pyodide/"):
            served.append(self.path)
            if not pyodide_up.is_set():
                self.send_error(503)
                return
        super().do_GET()

    def log_message(self, *args: object) -> None:
        pass


def serve() -> int:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Site, directory=str(ROOT / "site")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


def exercises(course: str) -> list[tuple[str, str, int, str]]:
    """(lesson, exercise, position of its panel in the step, step) for each exercise of the course."""
    found = []
    for path in sorted((ROOT / "site" / course / "lessons").glob("*/lesson.json")):
        lesson = json.loads(path.read_text(encoding="utf-8"))
        for number, beat in enumerate(lesson["beats"]):
            blocks = [b for b in beat["scene"] if b.get("type") == "exercise"]
            found += [(lesson["id"], b["exercise"], k, f"{number}") for k, b in enumerate(blocks)]
    return found


def open_panel(page: Page, base: str, course: str, lesson: str, step: str, k: int) -> Locator:
    page.goto(f"{base}/{course}/lesson.html?l={lesson}&beat={step}")
    panel = page.locator(".xpanel").nth(k)
    panel.locator(".cm-editor").wait_for()
    return panel


def write(page: Page, panel: Locator, code: str) -> None:
    panel.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.insert_text(code)


def verdict(page: Page, panel: Locator, code: str) -> dict[str, Any]:
    """Press «Comprobar» and read the result the page shows."""
    write(page, panel, code)
    panel.get_by_role("button", name="Comprobar").click()
    panel.locator(RESULT).wait_for(timeout=90_000)
    cases = panel.locator(".xtests li")
    return dict(
        passed=panel.locator(".xstatus.ok").count() == 1,
        flags=[c.get_attribute("class") or "" for c in cases.all()],
        texts=[c.inner_text() for c in cases.all()],
    )


def server_flags(eid: str, code: str) -> list[bool]:
    return [t["passed"] for t in grade(eid, code)["tests"]]


def parts(eid: str) -> tuple[str, str]:
    folder = spec.folder(eid)
    return (folder / "starter.py").read_text(encoding="utf-8"), (folder / "solution.py").read_text(
        encoding="utf-8"
    )


def physics(browser: Browser, base: str) -> None:
    """Every exercise: the starter fails, the solution passes, the server agrees, /run is untouched."""
    context = offline.new_context(browser, **DESKTOP)
    hits: list[str] = []

    def refuse(route: Route) -> None:
        hits.append(route.request.url)
        route.abort()

    context.route("**/run", refuse)
    errors: list[str] = []
    page = context.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    for lesson, eid, k, step in exercises(PHYSICS):
        starter, solution = parts(eid)
        panel = open_panel(page, base, PHYSICS, lesson, step, k)
        for label, code, passes in (("starter", starter, False), ("solution", solution, True)):
            got = verdict(page, panel, code)
            check(got["passed"] is passes, f"{eid}: the {label} {'passes' if passes else 'fails'}")
            flags = [("ok" in f.split()) for f in got["flags"]]
            check(
                flags == server_flags(eid, code),
                f"{eid}: the {label} passes the same cases as on the server",
            )
    check(not hits, f"/run was never requested ({hits})")
    check(not errors, f"no page errors {errors}")
    context.close()


def warm_cache(browser: Browser, base: str) -> None:
    """After one visit that downloaded Pyodide, a visit with the files gone from the network still grades."""
    lesson, eid, k, step = exercises(PHYSICS)[0]
    solution = parts(eid)[1]
    served.clear()
    context = offline.new_context(browser, **DESKTOP)
    page = context.new_page()
    page.goto(f"{base}/{PHYSICS}/")
    page.evaluate("navigator.serviceWorker.ready.then(() => 0)")
    page.reload()
    page.wait_for_function("!!navigator.serviceWorker.controller")
    before = len(served)
    check(before == 0, f"warm: a course page does not download Pyodide ({before} requests)")
    panel = open_panel(page, base, PHYSICS, lesson, step, k)
    check(verdict(page, panel, solution)["passed"], "warm: the first visit grades")
    check(len(served) > 0, "warm: the first visit downloaded the Pyodide files")
    caches = page.evaluate("caches.keys()")
    check(
        any(name.startswith("pyodide-") for name in caches),
        f"warm: the service worker keeps Pyodide in its own cache ({caches})",
    )
    pyodide_up.clear()
    second = context.new_page()
    panel = open_panel(second, base, PHYSICS, lesson, step, k)
    check(
        verdict(second, panel, solution)["passed"],
        "warm: with the Pyodide files gone from the network, the solution still passes",
    )
    pyodide_up.set()
    context.close()


def lazy_load(browser: Browser, base: str) -> None:
    """Pyodide loads only on an exercise page of the course, and only once the learner reaches the editor."""
    served.clear()
    context = offline.new_context(browser, **DESKTOP)
    page = context.new_page()
    for path in ("/", f"/{PHYSICS}/", "/qiskit/"):
        page.goto(base + path)
        page.wait_for_load_state("networkidle")
    lesson, _, k, step = exercises("qiskit")[0]
    open_panel(page, base, "qiskit", lesson, step, k)
    page.wait_for_load_state("networkidle")
    lesson, _, k, step = exercises(PHYSICS)[0]
    panel = open_panel(page, base, PHYSICS, lesson, step, k)
    page.wait_for_load_state("networkidle")
    check(
        not served,
        f"lazy: the home page, the course pages, a Qiskit exercise and an idle physics editor download nothing from Pyodide ({served[:3]})",
    )
    panel.locator(".cm-content").click()
    deadline = 20
    while not served and deadline:
        page.wait_for_timeout(250)
        deadline -= 1
    check(bool(served), "lazy: reaching the editor of a physics exercise starts the download")
    context.close()


def gate(browser: Browser, port: int) -> None:
    """Without a session a Qiskit exercise shows the sign-in links, and /run is never requested."""
    context = offline.new_context(
        browser,
        **DESKTOP,
    )
    base = f"http://{GATED_HOST}:{port}"
    posts: list[str] = []

    def runner(route: Route) -> None:
        posts.append(route.request.url)
        route.fulfill(status=401, json={"error": "signin_required"})

    context.route("**/run", runner)
    page = context.new_page()
    lesson, eid, k, step = exercises("qiskit")[0]
    panel = open_panel(page, base, "qiskit", lesson, step, k)
    solution = parts(eid)[1]
    links = panel.locator(".xgate a")
    check(links.count() == 2, "gate: the editor offers two ways to sign in")
    check(
        all("/auth/" in (h or "") for h in links.evaluate_all("els => els.map(e => e.href)")),
        "gate: each link starts a sign-in",
    )
    check(
        panel.locator("button", has_text="Comprobar").count() == 1
        and panel.locator("button", has_text="Comprobar").is_hidden()
        and panel.locator("button", has_text="Ejecutar").count() == 1
        and panel.locator("button", has_text="Ejecutar").is_hidden(),
        "gate: the run buttons are not shown",
    )
    check(panel.locator(".cm-editor").is_visible(), "gate: the exercise and its editor are shown")
    write(page, panel, solution)
    page.keyboard.press("ControlOrMeta+Enter")
    page.keyboard.press("ControlOrMeta+Shift+Enter")
    page.wait_for_timeout(1500)
    check(not posts, f"gate: the keyboard shortcuts do not reach /run ({posts})")
    check(panel.locator(RESULT).count() == 0, "gate: no result appears")
    context.close()


def main() -> None:
    port = serve()
    pyodide_up.set()
    base = f"http://localhost:{port}"
    with sync_playwright() as p:
        browser = p.chromium.launch(args=[f"--host-resolver-rules=MAP {GATED_HOST} 127.0.0.1"])
        offline.LOCAL_HOSTS.add(GATED_HOST)
        physics(browser, base)
        lazy_load(browser, base)
        warm_cache(browser, base)
        gate(browser, port)
        browser.close()
    offline.verify()
    print(f"\n{len(failures)} failures" if failures else "\nall good")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
