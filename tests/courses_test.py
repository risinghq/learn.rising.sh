import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_qiskit_note_matches_dependency_pin() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dependency = next(
        item for item in pyproject["project"]["dependencies"] if item.startswith("qiskit[")
    )
    _, separator, version = dependency.partition(">=")
    assert separator
    version = version.split(",", 1)[0].strip()

    courses = json.loads((ROOT / "site" / "courses.json").read_text())
    qiskit = next(course for course in courses if course["slug"] == "qiskit")
    assert qiskit["note"] == f"Todo el código se ejecutó con Qiskit {version}."
