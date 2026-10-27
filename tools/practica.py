"""Checks the marimo notebooks in practica/.

    uv run python tools/practica.py [notebook ...]

Each notebook runs as is and with the solutions in
practica/soluciones/<name>.json applied. The checks must give ✅ with the solutions.
If it has mo.ui.slider or mo.ui.number controls, it also runs with every control at its
minimum and at its maximum. Checks that give ❌ at an extreme are listed, but do not make the
run fail because they can depend on the parameters.
"""

import ast
import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PR = ROOT / "practica"


def veredictos(path: Path, carpeta: Path) -> list[tuple[str, str]]:
    """Run the notebook with its neighbouring modules available to import."""
    sys.path.insert(0, str(carpeta))
    try:
        spec = importlib.util.spec_from_file_location("nb_" + path.stem, path)
        assert spec and spec.loader
        nb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nb)
        with contextlib.redirect_stdout(io.StringIO()):
            outputs, _ = nb.app.run()
    finally:
        sys.path.remove(str(carpeta))
    text = " ".join(str(getattr(o, "text", o)) for o in outputs)
    return re.findall(r"(✅|❌)\s+([^<&]{0,60})", text)


def ejecutar(src: str, nombre: str, carpeta: Path) -> list[tuple[str, str]]:
    """Run src as notebook `nombre` with the modules of `carpeta` available."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / nombre
        tmp.write_text(src, encoding="utf-8")
        return veredictos(tmp, carpeta)


def con_extremo(src: str, extremo: str) -> tuple[str, dict[str, Any]]:
    """Replace the value= of each control with its minimum or maximum.

    Return the updated code and the values used, by control name.
    """
    lineas = src.encode("utf-8").split(b"\n")
    inicios = [0]
    for linea in lineas:
        inicios.append(inicios[-1] + len(linea) + 1)

    def pos(lineno: int, col: int) -> int:
        return inicios[lineno - 1] + col

    cambios: list[tuple[int, int, str]] = []
    valores: dict[str, Any] = {}
    for asig in ast.walk(ast.parse(src)):
        call = getattr(asig, "value", None)
        if not (
            isinstance(asig, ast.Assign)
            and isinstance(call, ast.Call)
            and ast.unparse(call.func) in ("mo.ui.slider", "mo.ui.number")
        ):
            continue
        nombre = ast.unparse(asig.targets[0])
        kw = {k.arg: k.value for k in call.keywords}
        limites = [ast.literal_eval(a) for a in call.args[:2]]
        limites += [ast.literal_eval(kw[k]) for k in ("start", "stop")[len(limites) :]]
        if "value" not in kw:
            raise ValueError(f"{nombre}: the control does not set value=")
        valor = limites[0 if extremo == "min" else 1]
        v = kw["value"]
        assert v.end_lineno is not None and v.end_col_offset is not None
        cambios.append(
            (pos(v.lineno, v.col_offset), pos(v.end_lineno, v.end_col_offset), repr(valor))
        )
        valores[nombre] = valor
    datos = src.encode("utf-8")
    for a, b, nuevo in sorted(cambios, reverse=True):
        datos = datos[:a] + nuevo.encode("utf-8") + datos[b:]
    return datos.decode("utf-8"), valores


def comprobar(f: Path) -> int:
    """Return 1 if the notebook fails, 0 if it passes or has no solutions."""
    rel = f.resolve().relative_to(PR.resolve()).as_posix()
    try:
        sin = veredictos(f, f.resolve().parent)
    except Exception as e:
        print(f"✗ {rel}: error unsolved: {e!r}")
        return 1
    solf = PR / "soluciones" / (rel.replace("/", "__").replace(".py", ".json"))
    if not solf.exists():
        print(f"? {rel}: no solutions ({len(sin)} checks)")
        return 0
    fallos = 0
    src = f.read_text(encoding="utf-8")
    for old, new in json.loads(solf.read_text(encoding="utf-8")):
        if old not in src:
            print(f"✗ {rel}: the solution does not find «{old}»")
            fallos += 1
        src = src.replace(old, new)
    carpeta = f.resolve().parent
    try:
        con = ejecutar(src, f.name, carpeta)
    except Exception as e:
        print(f"✗ {rel}: error with solutions: {e!r}")
        return fallos + 1
    malos = [m for s, m in con if s == "❌"]
    pend = sum(1 for s, _ in sin if s == "❌")
    if malos:
        print(f"✗ {rel}: still fails with solutions: {malos}")
        fallos += 1
    else:
        print(f"✓ {rel}: {pend} pending missions unsolved, all ✅ with solutions")
    for extremo in ("min", "max"):
        try:
            nuevo, valores = con_extremo(src, extremo)
            if not valores:
                break
            ext = ejecutar(nuevo, f.name, carpeta)
        except Exception as e:
            print(f"✗ {rel}: error at {extremo} with solutions: {e!r}")
            fallos += 1
            continue
        malos = [m for s, m in ext if s == "❌"]
        if malos:
            print(f"! {rel}: ❌ at {extremo} with {valores}: {malos}")
    return fallos


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    import matplotlib

    matplotlib.use(
        "Agg"
    )  # Stops Tk from freeing figures on another thread and aborting the process.
    files = [Path(a) for a in sys.argv[1:]] or sorted(
        p
        for p in PR.rglob("*.py")
        if "soluciones" not in p.parts and "marimo.App(" in p.read_text(encoding="utf-8")
    )
    fallos = sum(comprobar(f) for f in files)
    print("failures:", fallos)
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
