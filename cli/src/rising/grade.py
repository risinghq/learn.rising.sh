"""Grade the learner's file with qgcheck, using the cases that ship with the CLI."""

import os
import shutil
import tempfile
from importlib import resources
from pathlib import Path
from typing import Any

from qgcheck import grade

from rising.client import ApiError

TIMEOUT = 30


def run(exercise: str, code: str) -> dict[str, Any]:
    check = resources.files("rising") / "checks" / exercise / "check.py"
    if not check.is_file():
        raise ApiError(
            0, "unknown_exercise", f"Esta versión de rising no conoce {exercise}. Actualiza rising."
        )
    with tempfile.TemporaryDirectory(prefix="rising-") as work:
        target = Path(work) / exercise
        target.mkdir(parents=True)
        with resources.as_file(check) as source:
            shutil.copy(source, target / "check.py")
        os.environ["QG_EXERCISES"] = work
        return grade(exercise, code, mode="check", timeout=TIMEOUT)


def show(result: dict[str, Any]) -> None:
    """Print each check, then what the code printed and its error."""
    if result["stdout"]:
        print(result["stdout"].rstrip("\n"))
        print()
    for test in result["tests"]:
        print(f"{'✓' if test['passed'] else '✗'} {test['name']}")
        if not test["passed"] and test["message"]:
            print(f"    {test['message']}")
    if result["error"]:
        print(f"✗ {result['error']}")
    print("Pasó todos los casos." if result["passed"] else "Todavía no pasa todos los casos.")
