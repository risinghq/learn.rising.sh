"""What the grader knows about a learner's code before running it.

`preload` imports the scientific libraries that code and the cases use, so the processes forked
afterwards inherit them already loaded. `describe` gives the error of a run with the learner's line.
"""

import ast
import contextlib
import importlib
import traceback

CODE_NAME = "tu_codigo.py"
# Only these libraries are preloaded: the learner cannot lengthen startup with an import of their own.
PRELOAD_ROOTS = {
    "qiskit",
    "qiskit_aer",
    "qiskit_ibm_runtime",
    "numpy",
    "scipy",
    "matplotlib",
    "rustworkx",
    "sympy",
}
# Modules the qgcheck helpers import when called, by the name check.py requests them with.
HELPER_MODULES = {
    "counts": "qiskit.primitives",
    "aer_counts": "qiskit_aer.primitives",
    "state": "qiskit.quantum_info",
    "operator": "qiskit.quantum_info",
}
# Qiskit functions that import scipy.stats on first use. Preloading it keeps the checker and the
# learner's process from importing it each (0.5 s of CPU in the runner).
USES_SCIPY_STATS = {"random_unitary", "random_hermitian", "random_quantum_channel", "QuantumVolume"}


def imported_modules(source: str) -> set[str]:
    """Modules the code imports anywhere, and those the qgcheck helpers it requests need."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if {
            getattr(node, "id", None),
            getattr(node, "attr", None),
            getattr(node, "name", None),
        } & USES_SCIPY_STATS:
            found.add("scipy.stats")
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
            if node.module == "qgcheck":
                found.update(HELPER_MODULES[a.name] for a in node.names if a.name in HELPER_MODULES)
            else:
                found.update(f"{node.module}.{a.name}" for a in node.names)
    return found


def uses_inside(check_source: str) -> bool:
    """Whether `check.py` defines any function marked `@inside`, which runs in the learner's process."""
    try:
        tree = ast.parse(check_source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                target = decorator.func if isinstance(decorator, ast.Call) else decorator
                if getattr(target, "id", getattr(target, "attr", None)) == "inside":
                    return True
    return False


def preload(*sources: str) -> None:
    """Import the PRELOAD_ROOTS modules the given sources use. A failure shows when the code imports."""
    wanted = set().union(*map(imported_modules, sources))
    for name in sorted(wanted):
        if name.split(".")[0] in PRELOAD_ROOTS:
            with contextlib.suppress(Exception):
                importlib.import_module(name)


def describe(exc: BaseException, source: str) -> str:
    """Describe the error and, when applicable, the last line of the learner's code."""
    if isinstance(exc, SyntaxError) and exc.filename == CODE_NAME:
        lineno, text = exc.lineno, (exc.text or "").strip()
        return f"{type(exc).__name__}: {exc.msg} (línea {lineno}: {text})"
    lines = source.splitlines()
    where = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == CODE_NAME]
    msg = f"{type(exc).__name__}: {exc}"
    n = where[-1].lineno if where else None
    if n is not None:
        text = lines[n - 1].strip() if n <= len(lines) else ""
        return f"{msg} (línea {n}: {text})"
    return msg
