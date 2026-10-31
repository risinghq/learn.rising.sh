"""Find an exercise on the site and write it to the current directory."""

import re
from pathlib import Path
from typing import Any

from rising.client import ApiError, Client
from rising.store import WORKSPACE, save_workspace

ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*/[a-z0-9]+(-[a-z0-9]+)*")
STATEMENT = "enunciado.md"


def find(node: Any, exercise: str) -> dict[str, Any] | None:
    """The exercise block in a lesson.json, wherever the lesson nests it."""
    if isinstance(node, dict):
        if node.get("type") == "exercise" and node.get("exercise") == exercise:
            return node
        node = list(node.values())
    if isinstance(node, list):
        for item in node:
            if found := find(item, exercise):
                return found
    return None


def fetch(client: Client, exercise: str) -> dict[str, Any]:
    """The block of `exercise` in the lesson.json of the first course that has its lesson."""
    lesson = exercise.split("/")[0]
    for course in client.request("GET", "/courses.json"):
        try:
            block = find(
                client.request("GET", f"/{course['slug']}/lessons/{lesson}/lesson.json"), exercise
            )
        except ApiError as e:
            if e.status == 404:
                continue
            raise
        if block:
            return block
    raise ApiError(404, "unknown_exercise", f"No existe el ejercicio {exercise}.")


def write(exercise: str, block: dict[str, Any], force: bool) -> Path:
    """Write the starter, the statement and the marker `rising test` reads."""
    code = Path(f"{exercise.split('/')[1]}.py")
    clash = [p for p in (code, Path(STATEMENT), Path(WORKSPACE)) if p.exists()]
    if clash and not force:
        names = ", ".join(map(str, clash))
        raise ApiError(0, "exists", f"Ya existe {names}. Usa --force para reemplazarlo.")
    code.write_text(block["starter"].rstrip("\n") + "\n", encoding="utf-8")
    cases = "".join(f"- {name}\n" for name in block.get("cases", []))
    Path(STATEMENT).write_text(
        f"# {exercise}\n\n{block['prompt']}\n\n## Casos visibles\n\n{cases}", encoding="utf-8"
    )
    save_workspace(exercise, code.name)
    return code
