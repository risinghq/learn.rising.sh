"""Build hook: ships the check.py of each exercise inside the package.

`rising test` grades with these cases, so they travel with the CLI. The wheel gets them from
../exercises. The source distribution carries them under src/rising/checks, and a wheel built
from it finds them there as ordinary package files.
"""

from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class ChecksHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        exercises = Path(self.root).parent / "exercises"
        if not exercises.is_dir():
            return
        prefix = "src/rising/checks" if self.target_name == "sdist" else "rising/checks"
        for check in sorted(exercises.glob("*/*/check.py")):
            build_data["force_include"][str(check)] = f"{prefix}/{check.relative_to(exercises)}"
