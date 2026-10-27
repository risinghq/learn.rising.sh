"""Real playback test (with audio and timings): advances, answers the lesson's first two
questions (multiple-choice ones first wrong and then right) and moves to the next step.

    python -m http.server 8810 -d site          # in another terminal
    uv run --group tools python tools/playtest.py [lesson]

It uses Playwright's Chromium, which `mise run install` installs.
It leaves screenshots in shots/. PLAYTEST_URL changes the server address.
"""

import io
import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "shots"


def answerable(lesson: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    """(beat index, question) of the questions with a correct answer that can be answered."""
    return [
        (n, b["ask"])
        for n, b in enumerate(lesson["beats"])
        if b.get("ask", {}).get("kind") in ("choice", "numeric")
    ]


def answer(pg: Page, n: int, ask: dict[str, Any]) -> None:
    pg.locator("#timeline .seg").nth(n).click()
    pg.wait_for_selector("#ask.on", timeout=60000)
    if ask["kind"] == "choice":
        wrong = next(k for k in range(len(ask["options"])) if k != ask["right"])
        pg.click(f"#ask .opt >> nth={wrong}")
        print("wrong-answer feedback:", pg.inner_text("#ask .fb")[:60])
        pg.click(f"#ask .opt >> nth={ask['right']}")
    else:
        pg.fill("#ask input", str(ask["answer"]))
        pg.click("#ask .numrow .primary")
    print("right-answer feedback:", pg.inner_text("#ask .fb")[:60])
    pg.click("#ask .next-row .primary")
    pg.wait_for_timeout(1000)


def main() -> None:
    lesson_id = sys.argv[1] if len(sys.argv) > 1 else "p6-panorama"
    base_url = os.environ.get("PLAYTEST_URL", "http://localhost:8810").rstrip("/")
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lesson = json.loads(
        (ROOT / "site" / "qiskit" / "lessons" / lesson_id / "lesson.json").read_text(
            encoding="utf-8"
        )
    )
    SHOTS.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = b.new_page(viewport={"width": 1366, "height": 768})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(f"{base_url}/qiskit/lesson.html?l={lesson_id}")
        pg.wait_for_timeout(1500)
        print("start:", pg.inner_text("#start-meta"))
        pg.click("#go")
        pg.wait_for_timeout(4000)
        print("caption at t=4s:", pg.inner_text("#caption")[:70])
        pg.screenshot(path=str(SHOTS / "play-1.png"))
        for n, ask in answerable(lesson)[:2]:
            answer(pg, n, ask)
            print("after continuing:", pg.inner_text("#tag"))
        pg.screenshot(path=str(SHOTS / "play-2.png"))
        pg.click("#next")
        pg.wait_for_timeout(1500)
        print(
            "end visible:",
            pg.is_visible("#end"),
            "|",
            pg.inner_text("#end-score") if pg.is_visible("#end") else "",
        )
        pg.screenshot(path=str(SHOTS / "play-3.png"))
        print("errors:", errs or "none")
        b.close()


if __name__ == "__main__":
    main()
