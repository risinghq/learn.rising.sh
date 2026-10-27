"""Tests seeking inside a step: a click in the middle of a timeline segment.

    python -m http.server 8810 -d site          # in another terminal
    uv run --group tools python tools/seektest.py [lesson [step]]

By default it uses the third step («construir») of p1-composer, a list that is revealed item by item.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SHOTS = Path(__file__).resolve().parent.parent / "shots"
VISIBLE_ITEMS = (
    "[...document.querySelectorAll('#scene li')].filter(li => !li.classList.contains('hid')).length"
)


def main() -> None:
    lesson = sys.argv[1] if len(sys.argv) > 1 else "p1-composer"
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    url = f"http://localhost:8810/qiskit/lesson.html?l={lesson}"
    SHOTS.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = b.new_page(viewport={"width": 1366, "height": 768}, color_scheme="dark")
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url)
        pg.wait_for_timeout(1200)
        pg.click("#go")
        pg.wait_for_timeout(2500)
        box = pg.locator("#timeline .seg").nth(step).bounding_box()
        assert box is not None
        pg.mouse.click(box["x"] + box["width"] * 0.6, box["y"] + box["height"] / 2)
        pg.wait_for_timeout(1500)
        t = pg.evaluate("[window.QGNarration.currentTime, window.QGNarration.duration]")
        print("audio at", [round(x, 2) for x in t])
        print(
            "tag:",
            pg.inner_text("#tag"),
            "| visible list items:",
            pg.evaluate(VISIBLE_ITEMS),
        )
        print("caption:", pg.inner_text("#caption")[:80])
        pg.screenshot(path=str(SHOTS / "seek-1.png"))
        pg.keyboard.press("Shift+ArrowLeft")
        pg.wait_for_timeout(1200)
        print("after −5 s, visible items:", pg.evaluate(VISIBLE_ITEMS))
        pg.click("#fwd5")
        pg.wait_for_timeout(800)
        print("after +5 s, tag:", pg.inner_text("#tag"))
        done = pg.evaluate(
            "[...document.querySelectorAll('#timeline .seg')].map(s => s.className).join(' | ')"
        )
        print("segments:", done[:160])
        pg.goto(url)
        pg.wait_for_timeout(1000)
        print(
            "resume button:",
            pg.is_visible("#resume"),
            pg.inner_text("#resume") if pg.is_visible("#resume") else "",
        )
        print("errors:", errs or "none")
        b.close()


if __name__ == "__main__":
    main()
