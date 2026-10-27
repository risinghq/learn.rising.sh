"""Revisión visual: captura el estado final de cada beat (modo ?beat=N) y arma hojas de contacto.

    python -m http.server 8810 -d site          # en otra terminal
    uv run --group tools python tools/review.py [lección ...] [--port 8810]
Salida: shots/<lección>/NN-land.png, NN-port.png y shots/<lección>-hoja-{land,port}.png
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
COURSE, OUT = ROOT / "site" / "qiskit", ROOT / "shots"
SIZES = {"land": (1366, 768), "port": (390, 844)}

# Detecta bloques fuera del escenario o bajo la etiqueta superior.
OVERFLOW = """() => { const st = document.querySelector('#stage').getBoundingClientRect();
  const tag = document.querySelector('#tag').getBoundingClientRect();
  return [...document.querySelectorAll('#scene > .blk')].some(b => { const r = b.getBoundingClientRect();
    return r.height && (r.top < tag.bottom - 2 || r.bottom > st.bottom + 1 || r.left < st.left - 1 || r.right > st.right + 1); }); }"""


def watch(pg: Page, errors: dict[str, list[str]], lid: str) -> None:
    """Anota en `errors[lid]` los errores de página y de consola."""

    def note(message: str) -> None:
        errors.setdefault(lid, []).append(message)

    pg.on("pageerror", lambda e: note(str(e)))
    pg.on("console", lambda m: note(m.text) if m.type == "error" else None)


def sheet(files: list[Path], dest: Path, cols: int) -> None:
    ims = [Image.open(f) for f in files]
    w, h = ims[0].size
    sc = 0.5 if w > 1000 else 0.6
    tw, th = int(w * sc), int(h * sc)
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * tw, rows * (th + 22)), "white")
    d = ImageDraw.Draw(S)
    for k, (f, im) in enumerate(zip(files, ims, strict=True)):
        x, y = (k % cols) * tw, (k // cols) * (th + 22)
        S.paste(im.resize((tw, th)), (x, y + 22))
        d.text((x + 6, y + 4), f.stem, fill="black")
    S.save(dest)


def main() -> None:
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else "8810"
    ids = [a for a in sys.argv[1:] if not a.startswith("--") and a != port] or [
        les["id"]
        for p in json.loads((COURSE / "course.json").read_text(encoding="utf-8"))["parts"]
        for les in p["lessons"]
    ]
    errors: dict[str, list[str]] = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for lid in ids:
            les = json.loads((COURSE / "lessons" / lid / "lesson.json").read_text(encoding="utf-8"))
            if not (COURSE / "lessons" / lid / "timings.json").exists():
                print(lid, "sin timings, se omite")
                continue
            (OUT / lid).mkdir(parents=True, exist_ok=True)
            for tag, (w, h) in SIZES.items():
                pg = b.new_page(viewport={"width": w, "height": h})
                watch(pg, errors, lid)
                files: list[Path] = []
                for n, beat in enumerate(les["beats"]):
                    pg.goto(f"http://localhost:{port}/qiskit/lesson.html?l={lid}&beat={n}")
                    pg.wait_for_timeout(1700)
                    f = OUT / lid / f"{n:02d}-{beat['id']}-{tag}.png"
                    pg.screenshot(path=str(f))
                    files.append(f)
                    if pg.evaluate(OVERFLOW):
                        errors.setdefault(lid, []).append(f"desborde en {n:02d}-{beat['id']}-{tag}")
                pg.close()
                sheet(files, OUT / f"{lid}-hoja-{tag}.png", 3 if tag == "land" else 6)
            print(lid, "ok")
        b.close()
    print("errores:", json.dumps(errors, ensure_ascii=False, indent=1) if errors else "ninguno")


if __name__ == "__main__":
    main()
