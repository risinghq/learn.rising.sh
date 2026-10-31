"""Checks the exercises in exercises/ with qgcheck.

    uv run python tools/exercises.py [lesson/exercise ...]

For each exercise it checks that:
  1. solution.py passes every case of check.py.
  2. starter.py runs without error and fails some case: it never arrives solved.
  3. `needs` is true. With needs="python", solution.py passes without qiskit. With
     needs="qiskit", it passes without qiskit_aer. With needs="aer", it does not pass
     without it.
  4. Each `@hint(n)` in check.py names a hint that the exercise has in its lesson.
  5. A `kind="fix"` exercise starts from broken code, not an empty starter: starter.py keeps no
     `✏️` placeholder, is close to solution.py, and fails a case the learner sees.

`needs` is read from site/<course>/lessons/*/lesson.json, so run lessons_src/build.py first.
"""

import difflib
import io
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "lessons_src")]

from build import walk  # noqa: E402

from qgcheck import grade, spec  # noqa: E402

SITE = ROOT / "site"
# The modules an exercise must not need, by the `needs` it declares.
WITHOUT = {"python": ("qiskit", "qiskit_aer"), "qiskit": ("qiskit_aer",)}
# How much of solution.py a broken starter keeps. Below it the learner writes code, not fixes it.
FIX_SIMILARITY = 0.8


def published() -> dict[str, dict[str, Any]]:
    """Return the published exercise blocks of every course, by id."""
    found: dict[str, dict[str, Any]] = {}
    for f in sorted(SITE.glob("*/lessons/*/lesson.json")):
        for beat in json.loads(f.read_text(encoding="utf-8"))["beats"]:
            for blk in walk(beat["scene"]):
                if blk.get("type") == "exercise":
                    found[blk["exercise"]] = blk
    return found


def declared() -> dict[str, str]:
    """Return the dependencies declared by the published exercises."""
    return {eid: blk["needs"] for eid, blk in published().items()}


def failures(result: dict[str, Any]) -> str:
    """Return the messages of the failed cases or the code's error."""
    if result["error"]:
        return str(result["error"])
    return (
        "; ".join(f"{t['name']}: {t['message']}" for t in result["tests"] if not t["passed"])
        or "no cases"
    )


def fix_problems(broken: str, solution: str, starter: dict[str, Any]) -> list[str]:
    """Return what makes a starter a poor bug to find: a placeholder, a rewrite, a hidden failure."""
    found: list[str] = []
    if "✏️" in broken:
        found.append("starter.py has a ✏️ placeholder: a fix-it starter is code to repair")
    ratio = difflib.SequenceMatcher(None, broken, solution).ratio()
    if ratio < FIX_SIMILARITY:
        found.append(
            f"starter.py keeps {ratio:.0%} of solution.py; a fix-it starter keeps "
            f"{FIX_SIMILARITY:.0%} or more, so the learner fixes it instead of rewriting it"
        )
    if not any(t["visible"] and not t["passed"] for t in starter["tests"]):
        found.append("starter.py fails no case the learner sees: the bug has to show")
    return found


def problems(eid: str, needs: str, hints: int | None = None, kind: str = "write") -> list[str]:
    """Return the exercise's problems and validate its hint references."""
    d = spec.folder(eid)
    if missing := spec.missing_files(eid):
        return [f"missing {', '.join(missing)}"]
    solution = (d / "solution.py").read_text(encoding="utf-8")
    found: list[str] = []
    if hints is not None:
        for fn, _ in spec.load_cases(d / "check.py"):
            number = getattr(fn, "qg_hint", None)
            if number is not None and number > hints:
                found.append(f"{fn.__name__} names hint {number} and the exercise has {hints}")
    solved = grade(eid, solution)
    if not solved["passed"]:
        found.append(f"solution.py does not pass: {failures(solved)}")
    broken = (d / "starter.py").read_text(encoding="utf-8")
    starter = grade(eid, broken)
    if starter["error"]:
        found.append(f"starter.py fails to run: {starter['error']}")
    elif starter["passed"]:
        found.append("starter.py already passes every case")
    elif kind == "fix":
        found.extend(fix_problems(broken, solution, starter))
    if solved["passed"]:
        if needs in WITHOUT:
            without = grade(eid, solution, block=WITHOUT[needs])
            if not without["passed"]:
                found.append(
                    f'needs="{needs}" but solution.py needs {" or ".join(WITHOUT[needs])}: '
                    f"{failures(without)}"
                )
        else:
            if grade(eid, solution, block=("qiskit_aer",))["passed"]:
                found.append('needs="aer" but solution.py passes without qiskit_aer')
    return found


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    needs = declared()
    blocks = published()
    hints = {eid: len(blk["hints"]) for eid, blk in blocks.items()}
    ids = sys.argv[1:] or sorted(set(needs) | set(spec.all_ids()))
    bad = 0
    for eid in ids:
        if eid not in needs:
            print(f"✗ {eid}: no lesson uses it")
            bad += 1
            continue
        try:
            found = problems(
                eid, needs[eid], hints.get(eid), blocks.get(eid, {}).get("kind", "write")
            )
        except ValueError as exc:
            found = [str(exc)]
        for line in found:
            print(f"✗ {eid}: {line}")
        if not found:
            print(f"✓ {eid} ({needs[eid]})")
        bad += bool(found)
    print("failures:", bad)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
