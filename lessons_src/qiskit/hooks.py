"""What only the Qiskit course checks and adds, which build.py calls if a course has this module.

`check()` fails unless every guide of the Qiskit/documentation index (downloaded by
tools/fetch_docs.py) is in exactly one lesson of plan.PARTS. `references()` gives the lesson's
link to its original guides.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from plan import GUIDES, PARTS

ROOT = Path(__file__).resolve().parent.parent.parent
GUIDE = "https://quantum.cloud.ibm.com/docs/en/guides/"
TOC = ROOT / ".cache" / "qiskit-docs" / "docs" / "guides" / "_toc.json"


def toc_pages() -> list[str]:
    if not TOC.exists():
        raise SystemExit(f"missing {TOC.relative_to(ROOT)}: run python tools/fetch_docs.py")
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


def check() -> str:
    planned = [g for p in PARTS for _, _, gs in p["lessons"] for g in gs]
    planned.extend(g for _, _, gs in GUIDES for g in gs)
    dup = {g for g in planned if planned.count(g) > 1}
    missing = [g for g in toc_pages() if g not in planned]
    extra = [g for g in planned if g not in toc_pages()]
    if dup or missing or extra:
        raise SystemExit(
            f"coverage: repeated {sorted(dup)}, without lesson {missing}, nonexistent {extra}"
        )
    return f"coverage of the {len(toc_pages())} guides: complete"


def references(guides: Iterable[str]) -> list[str]:
    return [
        "Guías originales: "
        + " · ".join(f"[{g}]({GUIDE}{'' if g == 'index' else g})" for g in guides)
    ]
