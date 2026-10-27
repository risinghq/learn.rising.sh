"""Ejecuta el código Python que aparece en las lecciones, en orden, con un espacio de nombres por lección.

    uv run python tools/verify.py [lección ...]

Así se comprueba que todo el código que se enseña funciona con las versiones instaladas.
Si un bloque Out(…, check=True) sigue a un bloque de código en la misma escena, su texto debe
coincidir exactamente con lo que imprime ese código. Bloques con norun=True se omiten
(por ejemplo, los que necesitan una cuenta de IBM Quantum). Si un bloque trae setup="…", ese
código se ejecuta antes que el bloque, sin mostrarse: da el contexto a un fragmento.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import traceback
from collections.abc import Iterator
from pathlib import Path
from typing import Any

COURSE = Path(__file__).resolve().parent.parent / "site" / "qiskit"


def blocks(scene: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for s in scene:
        yield s
        yield from blocks(
            [x for x in s.get("items", []) + s.get("body", []) if isinstance(x, dict)]
        )


def verify_lesson(lid: str, show: bool) -> tuple[int, int]:
    """Ejecuta los bloques de una lección y devuelve (bloques ejecutados, fallos)."""
    les = json.loads((COURSE / "lessons" / lid / "lesson.json").read_text(encoding="utf-8"))
    ns: dict[str, Any] = {"__name__": "__leccion__"}
    n, fails = 0, 0
    for b in les["beats"]:
        bl = list(blocks(b["scene"]))
        for k, s in enumerate(bl):
            if s.get("type") != "code" or s.get("lang") != "python" or s.get("norun"):
                continue
            n += 1
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    if s.get("setup"):
                        exec(compile(s["setup"], f"{lid}/{b['id']}:setup", "exec"), ns)
                        buf.truncate(0)
                        buf.seek(0)
                    exec(compile(s["src"], f"{lid}/{b['id']}", "exec"), ns)
            except Exception:
                fails += 1
                print(f"✗ {lid}/{b['id']}\n{traceback.format_exc(limit=2)}")
                continue
            out = buf.getvalue().rstrip()
            nxt = bl[k + 1] if k + 1 < len(bl) else None
            if (
                nxt
                and nxt.get("type") == "code"
                and nxt.get("lang") == "out"
                and nxt.get("check")
                and out != nxt["src"].rstrip()
            ):
                fails += 1
                print(
                    f"✗ {lid}/{b['id']}: la salida no coincide\n--- esperado\n{nxt['src']}\n--- obtenido\n{out}"
                )
            if show:
                print(f"· {lid}/{b['id']}\n{out}")
    return n, fails


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    import matplotlib

    matplotlib.use("Agg")
    ids = [a for a in sys.argv[1:] if not a.startswith("-")] or [
        les["id"]
        for p in json.loads((COURSE / "course.json").read_text(encoding="utf-8"))["parts"]
        for les in p["lessons"]
    ]
    show = "-v" in sys.argv or "--show" in sys.argv
    fails = 0
    os.chdir(
        tempfile.mkdtemp(prefix="verify-")
    )  # Aísla los archivos temporales que crean los ejemplos.
    for lid in ids:
        n, f = verify_lesson(lid, show)
        fails += f
        print(f"{lid}: {n} bloques ejecutados")
    print("fallos:", fails)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
