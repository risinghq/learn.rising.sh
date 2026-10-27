"""Check the optional account in a browser with a local Worker and a fake provider.

    uv run --group tools python tests/account_ui_test.py

Check the sync between two browsers and that deleting the account keeps the
local copy. Without an account, the page makes only its own `/run` request.
The test skips with the reason when Node or the Worker dependencies are missing.
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
# The fake runner fails a check whose code contains FALLA.
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
        raise RuntimeError(f"the local Worker did not start: {process.stderr.read()}")
    return process, json.loads(line)


def last_beat(lesson: str) -> int:
    beats = json.loads(
        (ROOT / "site" / "qiskit" / "lessons" / lesson / "lesson.json").read_text(encoding="utf-8")
    )["beats"]
    return len(beats) - 1


def new_page(browser: Browser, site: str, control: str) -> Tab:
    """A new browser: the Turnstile widget and the provider screen are fake."""
    context = new_context(browser, **DESKTOP)
    context.route(
        "https://challenges.cloudflare.com/turnstile/v0/api.js*",
        lambda r: r.fulfill(content_type="text/javascript", body=FAKE_TURNSTILE),
    )

    def provider(route: Route) -> None:
        """The Worker redirects to the provider. The browser does not follow that redirect through
        route, so this handler answers for the provider: the learner approves and returns to the
        redirect address with the code."""
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
    check(panel.locator(".xstatus.bad").count() == 1, "anonymous: the check fails")
    page.goto(f"{site}/qiskit/lesson.html?l={LESSON}&beat={last_beat(LESSON)}")
    page.locator("#next").click()
    page.locator("#end:not(.hide)").wait_for()
    check(
        stored(page, "qiskit:done") == [LESSON],
        "anonymous: the lesson is marked done in the browser",
    )
    record = stored(page, f"qiskit:exercise:{EXERCISE}")
    check(
        record["code"] == FAILING
        and record["checks"] == 1
        and not record.get("passed")
        and record["at"] > 0,
        f"anonymous: the exercise stores the code, one failed check and the time ({record})",
    )
    page.wait_for_timeout(2500)
    ours = {
        (m, p.split("?")[0].split("#")[0])
        for m, p in requests
        if p.startswith(("/api", "/auth", "/health")) or m != "GET"
    }
    check(
        ours == {("POST", "/run")},
        f"anonymous: the only own request that is not a file is /run ({sorted(ours)})",
    )
    check(
        stored(page, "qiskit:hitos") == [1], "anonymous: the ticked milestone stays in the browser"
    )
    check(
        page.locator(".acct > button").first.inner_text() == "Entrar",
        "anonymous: the menu offers sign-in",
    )
    return page, errors, requests


def main() -> None:
    if not shutil.which("node") or not (WORKER / "node_modules" / "miniflare").is_dir():
        print("skipped: needs node and `mise run install`")
        return
    worker, urls = start_worker()
    site, control = urls["site"], urls["control"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            one, one_errors, one_requests = anonymous(browser, site, control)
            check(
                call(f"{control}/rows")["users"] == 0,
                "anonymous: the server has no account",
            )

            one.goto(f"{site}/qiskit/lesson.html?l={LESSON}&beat={last_beat(LESSON)}")
            sign_in(one)
            rows = call(f"{control}/rows")
            check(
                rows["users"] == 1
                and rows["lesson_done"] == 1
                and rows["exercise_state"] == 1
                and rows["kv"] == 1,
                f"on sign-in: the account stores the lesson, the exercise and the milestone ({rows})",
            )
            check(
                stored(one, "qiskit:done") == [LESSON]
                and stored(one, f"qiskit:exercise:{EXERCISE}")["code"] == FAILING,
                "on sign-in: the local copy is kept",
            )

            two, two_errors, _ = new_page(browser, site, control)
            two.goto(f"{site}/qiskit/index.html")
            sign_in(two)
            two.locator("#parts .part").first.wait_for()
            check(
                two.locator("#prog").inner_text().startswith("1/"),
                f"other browser: the front page counts the lesson as done ({two.locator('#prog').inner_text()})",
            )
            check(
                two.locator("#track .hito.done").count() == 1,
                "other browser: the front page ticks the milestone",
            )
            panel = open_panel(two, site, LESSON, 1)
            check(
                editor_text(panel) == unblank(FAILING),
                "other browser: the editor loads the code from the first one",
            )
            check(
                stored(two, f"qiskit:exercise:{EXERCISE}")["checks"] == 1,
                "other browser: it loads the failed check",
            )

            with two.expect_response(lambda r: r.url.endswith("/api/progress") and r.status == 204):
                write(two, panel, REWRITTEN)
            panel = open_panel(one, site, LESSON, 1)
            check(
                editor_text(panel) == unblank(REWRITTEN),
                "on load: the most recent code of the account wins",
            )

            menu(one, "Cuenta ✓")
            menu(one, "Borrar mi cuenta")
            menu(one, "Sí, borrar")
            one.get_by_role("button", name="Entrar", exact=True).wait_for()
            rows = call(f"{control}/rows")
            check(all(n == 0 for n in rows.values()), f"delete: the server is left empty ({rows})")
            check(
                stored(one, "qiskit:done") == [LESSON]
                and stored(one, f"qiskit:exercise:{EXERCISE}")["code"] == REWRITTEN,
                "delete: the local copy stays",
            )
            me = one.context.request.get(f"{site}/api/me").json()
            check(me == {"signedIn": False}, f"delete: the session was closed ({me})")
            before = len(one_requests)
            one.reload()
            one.locator(".xpanel").nth(1).locator(".cm-editor").wait_for()
            after = [r for r in one_requests[before:] if r[1].startswith(("/api", "/auth"))]
            check(not after, f"delete: the page no longer talks to the account ({after})")

            for errors in (one_errors, two_errors):
                check(not errors, f"no page errors {errors}")
            browser.close()
    finally:
        worker.terminate()
        worker.wait(timeout=30)
    verify()
    print(f"\n{len(failures)} failures" if failures else "\nall good")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
