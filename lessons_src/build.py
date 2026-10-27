"""Genera site/qiskit/lessons/<id>/lesson.json y site/qiskit/course.json a partir de plan.py y de los módulos parte*.py.

    python lessons_src/build.py              # escribe los JSON y comprueba la cobertura de las guías
    python lessons_src/build.py --check      # no escribe: falla si los JSON de site/qiskit/ no coinciden con lo que se generaría
    python lessons_src/build.py --tts        # además genera la narración (necesita uv, red y ffprobe)

La cobertura se comprueba contra .cache/qiskit-docs.
tools/fetch_docs.py descarga esa caché.

La numeración de secciones (1.1, 1.2, …) sale del orden de plan.PARTS; la primera parte de la
etiqueta de cada paso se sustituye por esa sección. Cada lección del plan debe tener su módulo, y
cada lección de un módulo debe estar en el plan.
"""

import importlib
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from plan import PARTS  # noqa: E402

from qgcheck import spec  # noqa: E402

COURSE = ROOT / "site" / "qiskit"
GUIDE = "https://quantum.cloud.ibm.com/docs/en/guides/"
TOC = ROOT / ".cache" / "qiskit-docs" / "docs" / "guides" / "_toc.json"


def load_lessons() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for f in sorted(HERE.glob("parte*.py")):
        for les in importlib.import_module(f.stem).LESSONS:
            if les["id"] in found:
                raise SystemExit(f"lección duplicada: {les['id']}")
            found[les["id"]] = les
    return found


def toc_pages() -> list[str]:
    if not TOC.exists():
        raise SystemExit(f"falta {TOC.relative_to(ROOT)}: ejecuta python tools/fetch_docs.py")
    toc = json.loads(TOC.read_text(encoding="utf-8"))
    out: list[str] = []

    def walk(n: dict[str, Any]) -> None:
        for c in n.get("children", []):
            u = c.get("url", "")
            if u == "/docs/guides":
                out.append("index")
            elif u.startswith("/docs/guides/"):
                out.append(u.rsplit("/", 1)[1])
            walk(c)

    walk(toc)
    return list(dict.fromkeys(out))


def coverage() -> None:
    planned = [g for p in PARTS for _, _, gs in p["lessons"] for g in gs]
    dup = {g for g in planned if planned.count(g) > 1}
    missing = [g for g in toc_pages() if g not in planned]
    extra = [g for g in planned if g not in toc_pages()]
    if dup or missing or extra:
        raise SystemExit(
            f"cobertura: repetidas {sorted(dup)}, sin lección {missing}, inexistentes {extra}"
        )


ERRORS: list[str] = []


def walk(blocks: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Recorre bloques de escena, incluidos los anidados en filas y cajas."""
    for blk in blocks:
        yield blk
        children = blk.get("items", []) + blk.get("body", [])
        yield from walk(x for x in children if isinstance(x, dict))


def publish_exercises(lesson: dict[str, Any], seen: set[str]) -> None:
    """Añade a cada ejercicio el código inicial y los casos visibles."""
    for b in lesson["beats"]:
        for blk in walk(b["scene"]):
            if blk.get("type") != "exercise":
                continue
            eid = blk["exercise"]
            where = f"{lesson['id']}/{b['id']}: ejercicio {eid}"
            try:
                missing = spec.missing_files(eid)
            except ValueError as exc:
                ERRORS.append(f"{where}: {exc}")
                continue
            if not eid.startswith(lesson["id"] + "/"):
                ERRORS.append(f"{where} debe estar en exercises/{lesson['id']}/")
            elif eid in seen:
                ERRORS.append(f"{where} está repetido")
            elif missing:
                ERRORS.append(f"{where} no tiene {', '.join(missing)}")
            else:
                seen.add(eid)
                blk.update(spec.public(eid))
                if not blk["cases"]:
                    ERRORS.append(f"{where} no tiene ningún caso @visible en check.py")


def check(lesson: dict[str, Any]) -> None:
    """Errores de autoría que conviene detectar antes de generar audio (se acumulan en ERRORS)."""

    def fail(msg: str) -> None:
        ERRORS.append(msg)

    for b in lesson["beats"]:
        marks = re.findall(r"\[\[(\w+)\]\]", b["say"])
        if len(marks) != len(set(marks)):
            fail(f"{lesson['id']}/{b['id']}: marca repetida")
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
                del a["at"]  # at=<id del paso> significa «al empezar el paso»
            if a.get("at") and a["at"] not in marks:
                fail(f"{lesson['id']}/{b['id']}: marca '{a['at']}' no está en la narración")
            if a.get("id") and a["id"] not in ids:
                fail(f"{lesson['id']}/{b['id']}: objeto '{a['id']}' no existe")
    if len({b["id"] for b in lesson["beats"]}) != len(lesson["beats"]):
        fail(f"{lesson['id']}: ids de paso repetidos")


def main() -> None:
    coverage()
    lessons = load_lessons()
    planned = {lid for part in PARTS for lid, _, _ in part["lessons"]}
    if planned != set(lessons):
        raise SystemExit(
            f"plan y módulos no coinciden: sin módulo {sorted(planned - set(lessons))}, "
            f"fuera del plan {sorted(set(lessons) - planned)}"
        )
    course: dict[str, Any] = dict(parts=[])
    ordered: list[dict[str, Any]] = []
    exercises: set[str] = set()
    for part in PARTS:
        entry: dict[str, Any] = dict(title=part["title"], desc=part["desc"], lessons=[])
        for k, (lid, _title, guides) in enumerate(part["lessons"], 1):
            section = f"{part['n']}.{k}"
            les = lessons[lid]
            les["part"], les["section"] = part["title"], section
            for b in les["beats"]:
                b["tag"][0] = section
            names = {g: g for g in guides}
            les["practice"] = [
                *les["practice"],
                "Guías originales: "
                + " · ".join(f"[{g}]({GUIDE}{'' if g == 'index' else g})" for g in names),
            ]
            check(les)
            publish_exercises(les, exercises)
            ordered.append(les)
            tf = COURSE / "lessons" / lid / "timings.json"
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
            missions = [
                blk
                for b in les["beats"]
                for blk in walk(b["scene"])
                if blk.get("type") == "mission"
            ]
            if missions:
                item["missions"] = [
                    dict(
                        notebook=m["notebook"],
                        title=m.get("title", "Tu turno"),
                        tasks=len(m["tasks"]),
                    )
                    for m in missions
                ]
            entry["lessons"].append(item)
        course["parts"].append(entry)
    ERRORS.extend(
        f"exercises/{eid} no aparece en ninguna lección"
        for eid in sorted(set(spec.all_ids()) - exercises)
    )
    if ERRORS:
        raise SystemExit("\n".join(ERRORS))
    outputs: dict[Path, str] = {}
    for a, b in zip(ordered, [*ordered[1:], None], strict=True):
        a["next"] = b["id"] if b else None
        outputs[COURSE / "lessons" / a["id"] / "lesson.json"] = json.dumps(
            a, ensure_ascii=False, indent=1
        )
    outputs[COURSE / "course.json"] = json.dumps(course, ensure_ascii=False, indent=1)
    if "--check" in sys.argv:
        stale = [
            p.relative_to(ROOT).as_posix()
            for p, text in outputs.items()
            if not p.exists() or p.read_text(encoding="utf-8") != text
        ]
        if stale:
            raise SystemExit(
                f"{len(stale)} archivos generados desactualizados; ejecuta `mise run generate` y súbelos:\n  "
                + "\n  ".join(stale)
            )
        print(f"{len(outputs)} archivos generados al día")
        return
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    total = sum(len(p["lessons"]) for p in PARTS)
    print(
        f"{len(ordered)} de {total} lecciones escritas, {sum(len(les['beats']) for les in ordered)} pasos; "
        f"cobertura de las {len(toc_pages())} guías: completa"
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
                    str(COURSE / "lessons" / les["id"]),
                ],
                check=True,
                cwd=ROOT,
            )


if __name__ == "__main__":
    main()
