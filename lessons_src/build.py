"""Generates site/<course>/lessons/<id>/lesson.json and site/<course>/course.json from the course's
plan.py and parte*.py modules.

    python lessons_src/build.py qiskit           # writes the JSON and runs the course's own checks
    python lessons_src/build.py qiskit --check   # writes nothing: fails if the JSON in site/qiskit/ differs from what would be generated
    python lessons_src/build.py qiskit --tts     # also generates the narration (needs uv, network and ffprobe)

<course> is the folder name in site/. Its source is lessons_src/<course>/, with dashes written as
underscores so that the folder is a Python package name. That folder holds plan.py (PARTS: each
lesson is (id, title) or (id, title, sources)), parte*.py (LESSONS) and, if the course checks more
than its lessons, hooks.py with `check() -> str` and `references(sources) -> list[str]`.

The section numbering (1.1, 1.2, …) comes from the order of plan.PARTS; the first part of
each step's label is replaced by that section. Every lesson in the plan must have its module, and
every lesson in a module must be in the plan. A lesson id belongs to one course: the browser and
the account store progress by lesson id.

plan.py may set RUNS = "browser" for a course whose exercises run and are graded in the learner's
browser on Pyodide, with no call to the runner. The default is "server". Such an exercise carries
its check.py in lesson.json, so the page grades with the same cases the server would, and it may
need only numpy, scipy and matplotlib (needs="python") and no `@inside` function.
"""

import importlib
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

from qgcheck import spec  # noqa: E402
from qgcheck.source import uses_inside  # noqa: E402

SITE = ROOT / "site"


def source_dir(course: str) -> Path:
    return HERE / course.replace("-", "_")


def load_lessons(source: Path) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for f in sorted(source.glob("parte*.py")):
        for les in importlib.import_module(f.stem).LESSONS:
            if les["id"] in found:
                raise SystemExit(f"duplicate lesson: {les['id']}")
            found[les["id"]] = les
    return found


def other_lesson_ids(course: str) -> dict[str, str]:
    """Lesson id -> course, for the lessons of the other courses in site/."""
    found: dict[str, str] = {}
    for path in sorted(SITE.glob("*/course.json")):
        if path.parent.name == course:
            continue
        for part in json.loads(path.read_text(encoding="utf-8"))["parts"]:
            for les in part["lessons"]:
                found[les["id"]] = path.parent.name
    return found


ERRORS: list[str] = []


def walk(blocks: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Walk scene blocks, including those nested in rows and boxes."""
    for blk in blocks:
        yield blk
        children = blk.get("items", []) + blk.get("body", [])
        yield from walk(x for x in children if isinstance(x, dict))


def publish_exercises(lesson: dict[str, Any], seen: set[str], runs: str) -> None:
    """Add the starter code and the visible cases to each exercise, and in a browser course the
    whole check.py: the hidden cases of that course are readable by the learner."""
    for b in lesson["beats"]:
        for blk in walk(b["scene"]):
            if blk.get("type") != "exercise":
                continue
            eid = blk["exercise"]
            where = f"{lesson['id']}/{b['id']}: exercise {eid}"
            try:
                missing = spec.missing_files(eid)
            except ValueError as exc:
                ERRORS.append(f"{where}: {exc}")
                continue
            if not eid.startswith(lesson["id"] + "/"):
                ERRORS.append(f"{where} must be in exercises/{lesson['id']}/")
            elif eid in seen:
                ERRORS.append(f"{where} is repeated")
            elif missing:
                ERRORS.append(f"{where} has no {', '.join(missing)}")
            else:
                seen.add(eid)
                blk.update(spec.public(eid))
                if not blk["cases"]:
                    ERRORS.append(f"{where} has no @visible case in check.py")
                if runs == "browser":
                    publish_browser(blk, where)


def publish_browser(blk: dict[str, Any], where: str) -> None:
    text = (spec.folder(blk["exercise"]) / "check.py").read_text(encoding="utf-8")
    if blk["needs"] != "python":
        ERRORS.append(f'{where}: the browser has no {blk["needs"]}, only needs="python"')
    if uses_inside(text):
        ERRORS.append(f"{where}: check.py uses @inside, which needs the server's second process")
    blk.update(runs="browser", check=text)


def check(lesson: dict[str, Any]) -> None:
    """Authoring errors worth catching before generating audio (they accumulate in ERRORS)."""

    def fail(msg: str) -> None:
        ERRORS.append(msg)

    for b in lesson["beats"]:
        marks = re.findall(r"\[\[(\w+)\]\]", b["say"])
        if len(marks) != len(set(marks)):
            fail(f"{lesson['id']}/{b['id']}: repeated mark")
        ids: set[str] = set()

        def collect(items: list[dict[str, Any]], ids: set[str] = ids) -> None:
            for s in items:
                if s.get("id"):
                    ids.add(s["id"])
                collect(
                    [x for x in s.get("items", []) + s.get("body", []) if isinstance(x, dict)],
                    ids,
                )

        collect(b["scene"])
        for a in b["actions"]:
            if a.get("at") == b["id"] and a["at"] not in marks:
                del a["at"]  # at=<step id> means «when the step starts»
            if a.get("at") and a["at"] not in marks:
                fail(f"{lesson['id']}/{b['id']}: mark '{a['at']}' is not in the narration")
            if a.get("id") and a["id"] not in ids:
                fail(f"{lesson['id']}/{b['id']}: object '{a['id']}' does not exist")
    if len({b["id"] for b in lesson["beats"]}) != len(lesson["beats"]):
        fail(f"{lesson['id']}: repeated step ids")


def main(course: str) -> None:
    source = source_dir(course)
    if not (source / "plan.py").is_file():
        raise SystemExit(f"no course {course!r}: missing {source.relative_to(ROOT)}/plan.py")
    sys.path.insert(0, str(source))
    plan = importlib.import_module("plan")
    parts: list[dict[str, Any]] = plan.PARTS
    runs: str = getattr(plan, "RUNS", "server")
    if runs not in ("server", "browser"):
        raise SystemExit(f"{course}: RUNS must be 'server' or 'browser', not {runs!r}")
    hooks: ModuleType | None = (
        importlib.import_module("hooks") if (source / "hooks.py").is_file() else None
    )
    out = SITE / course
    notes = [hooks.check()] if hooks else []
    lessons = load_lessons(source)
    planned = {lesson[0] for part in parts for lesson in part["lessons"]}
    if planned != set(lessons):
        raise SystemExit(
            f"plan and modules do not match: without module {sorted(planned - set(lessons))}, "
            f"outside the plan {sorted(set(lessons) - planned)}"
        )
    taken = other_lesson_ids(course)
    if clash := sorted(planned & set(taken)):
        raise SystemExit(f"lesson ids already used by another course: {clash}")
    course_json: dict[str, Any] = dict(parts=[])
    ordered: list[dict[str, Any]] = []
    exercises: set[str] = set()
    for part in parts:
        entry: dict[str, Any] = dict(title=part["title"], desc=part["desc"], lessons=[])
        for k, (lid, _title, *rest) in enumerate(part["lessons"], 1):
            section = f"{part['n']}.{k}"
            les = lessons[lid]
            les["part"], les["section"] = part["title"], section
            for b in les["beats"]:
                b["tag"][0] = section
            if hooks:
                les["practice"] = [*les["practice"], *hooks.references(rest[0] if rest else [])]
            check(les)
            publish_exercises(les, exercises, runs)
            ordered.append(les)
            tf = out / "lessons" / lid / "timings.json"
            beat_ids = {b["id"] for b in les["beats"]}
            if tf.exists():
                secs = sum(
                    v["dur"]
                    for key, v in json.loads(tf.read_text(encoding="utf-8")).items()
                    if key in beat_ids
                )
            else:
                secs = sum(len(b["say"].split()) for b in les["beats"]) / 140 * 60
            secs += 45 * sum(1 for b in les["beats"] if "ask" in b)
            item: dict[str, Any] = dict(
                id=lid,
                section=section,
                title=les["title"],
                summary=les["summary"],
                minutes=round(secs / 60),
            )
            entry["lessons"].append(item)
        course_json["parts"].append(entry)
    ERRORS.extend(
        f"exercises/{eid} does not appear in any lesson"
        for eid in sorted(spec.all_ids())
        if eid not in exercises and eid.split("/")[0] not in set(taken)
    )
    if ERRORS:
        raise SystemExit("\n".join(ERRORS))
    outputs: dict[Path, str] = {}
    for a, b in zip(ordered, [*ordered[1:], None], strict=True):
        a["next"] = b["id"] if b else None
        outputs[out / "lessons" / a["id"] / "lesson.json"] = json.dumps(
            a, ensure_ascii=False, indent=1
        )
    outputs[out / "course.json"] = json.dumps(course_json, ensure_ascii=False, indent=1)
    if "--check" in sys.argv:
        stale = [
            p.relative_to(ROOT).as_posix()
            for p, text in outputs.items()
            if not p.exists() or p.read_text(encoding="utf-8") != text
        ]
        if stale:
            raise SystemExit(
                f"{len(stale)} generated files are out of date; run `mise run generate` and commit them:\n  "
                + "\n  ".join(stale)
            )
        print(f"{course}: {len(outputs)} generated files up to date")
        return
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(
        f"{course}: {len(ordered)} lessons written, "
        f"{sum(len(les['beats']) for les in ordered)} steps" + "".join(f"; {n}" for n in notes)
    )
    if "--tts" in sys.argv:
        for les in ordered:
            subprocess.run(
                [
                    "uv",
                    "run",
                    "--group",
                    "tools",
                    "python",
                    str(ROOT / "tools" / "tts.py"),
                    str(out / "lessons" / les["id"]),
                ],
                check=True,
                cwd=ROOT,
            )


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(names) != 1:
        raise SystemExit("usage: build.py <course> [--check] [--tts]")
    main(names[0])
