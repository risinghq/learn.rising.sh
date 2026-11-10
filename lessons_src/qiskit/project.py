from copy import deepcopy
from typing import Any


def move_project_exercises(source: dict[str, Any], target: dict[str, Any], target_id: str) -> None:
    source_beat = next(beat for beat in source["beats"] if beat["id"] == "proyecto")
    moved = deepcopy(source_beat)
    exercise_ids = {
        block["id"] for block in source_beat["scene"] if block.get("type") == "exercise"
    }
    source_beat["scene"] = [
        block for block in source_beat["scene"] if block.get("type") != "exercise"
    ]
    source_beat["actions"] = [
        action for action in source_beat["actions"] if action.get("id") not in exercise_ids
    ]
    moved["id"] = target_id
    target["beats"].append(moved)
