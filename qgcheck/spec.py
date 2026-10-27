"""Locate an exercise in exercises/ and read from check.py the cases and what build.py publishes.

exercises/<lesson>/<exercise>/ holds starter.py (what the learner sees), solution.py (the
reference) and check.py (the cases). Only starter.py and the names of the visible cases reach
site/.
"""

import importlib.util
import os
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FILES = ("starter.py", "solution.py", "check.py")
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*")


def exercises_dir() -> Path:
    return Path(os.environ.get("QG_EXERCISES") or ROOT / "exercises")


def folder(exercise_id: str) -> Path:
    """Return the folder and reject ids that do not follow the published format."""
    if not ID.fullmatch(exercise_id):
        raise ValueError(f"invalid exercise id: {exercise_id!r}")
    return exercises_dir() / exercise_id


def all_ids() -> list[str]:
    """Return the ids of the exercise folders, sorted."""
    base = exercises_dir()
    return sorted(d.relative_to(base).as_posix() for d in base.glob("*/*") if d.is_dir())


def missing_files(exercise_id: str) -> list[str]:
    d = folder(exercise_id)
    return [f for f in FILES if not (d / f).is_file()]


def load_module(check_path: Path) -> ModuleType:
    """Import check.py, which must not read `learner` or run learner code when imported."""
    spec = importlib.util.spec_from_file_location("check", check_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cases(check_path: Path) -> list[tuple[Callable[..., Any], str | None]]:
    """[(function, visible name or None)] of each test_* in check.py, in definition order."""
    module = load_module(check_path)
    return [
        (fn, getattr(fn, "qg_visible", None))
        for name, fn in vars(module).items()
        if name.startswith("test_") and callable(fn)
    ]


def public(exercise_id: str) -> dict[str, Any]:
    """Return the starter code and the names of the visible cases."""
    d = folder(exercise_id)
    return dict(
        starter=(d / "starter.py").read_text(encoding="utf-8").rstrip("\n"),
        cases=[name for _, name in load_cases(d / "check.py") if name],
    )
