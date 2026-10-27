"""Screenshots of a lesson at several sizes, at chosen beats.

    python -m http.server 8810 -d site          # in another terminal
    uv run --group tools python tools/shot.py <id> <beat,beat,...> [movil|laptop] [wait ms]
Example: tools/shot.py p1-quickstart 0,3,8 laptop
Writes shots/<size>-b<beat>.png.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SIZES = {"movil": (390, 844), "laptop": (1366, 768)}


def main() -> None:
    lid = sys.argv[1]
    beats = [int(b) for b in sys.argv[2].split(",")]
    which = sys.argv[3] if len(sys.argv) > 3 else "laptop"
    wait = int(sys.argv[4]) if len(sys.argv) > 4 else 9000
    w, h = SIZES[which]
    out = Path(__file__).resolve().parent.parent / "shots"
    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = b.new_page(viewport={"width": w, "height": h})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(f"http://localhost:8810/qiskit/lesson.html?l={lid}")
        pg.wait_for_timeout(1200)
        pg.click("#go")
        cur = 0
        for t in beats:
            while cur < t:
                pg.click("#next")
                cur += 1
            pg.wait_for_timeout(wait)
            pg.screenshot(path=str(out / f"{which}-b{t}.png"))
        print("errors:", errs)
        b.close()


if __name__ == "__main__":
    main()
