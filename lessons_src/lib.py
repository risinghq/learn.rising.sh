"""Ayudantes para escribir lecciones en Python (cadenas crudas para LaTeX y código).

Cada módulo de contenido define LESSONS: una lista de dicts creados con lesson().
build.py los escribe en site/qiskit/lessons/<id>/lesson.json y genera site/qiskit/course.json.
"""

from collections.abc import Iterable
from typing import Any

Block = dict[str, Any]


def T(text: str, style: str = "body", **k: Any) -> Block:
    return dict(type="text", text=text, style=style, **k)


def M(tex: str, **k: Any) -> Block:
    return dict(type="math", tex=tex, **k)


def L(items: list[Any], **k: Any) -> Block:
    return dict(type="list", items=items, **k)


def Row(*items: Any, **k: Any) -> Block:
    return dict(type="row", items=list(items), **k)


def Box(kind: str, title: str, *body: Any, **k: Any) -> Block:
    return dict(type="box", kind=kind, title=title, body=list(body), **k)


def Plot(**k: Any) -> Block:
    return dict(type="plot", **k)


def Plane(**k: Any) -> Block:
    return dict(type="plane", **k)


def Code(src: str, lang: str = "python", **k: Any) -> Block:
    """Código con resaltado. reveal=True oculta las líneas hasta la acción 'lines'.
    norun=True excluye un bloque de Python de tools/verify.py cuando necesita una cuenta de IBM.
    setup="…" aporta el contexto de un fragmento. tools/verify.py lo ejecuta antes del bloque y la página no lo muestra."""
    return dict(type="code", src=src.strip(chr(10)), lang=lang, **k)


def Out(src: str, **k: Any) -> Block:
    """Salida de consola (texto tal como lo imprime Python)."""
    return dict(type="code", src=src.strip(chr(10)), lang="out", **k)


def Sh(src: str, **k: Any) -> Block:
    return dict(type="code", src=src.strip(chr(10)), lang="sh", **k)


def Circ(qubits: int, ops: list[Block], **k: Any) -> Block:
    """Diagrama de circuito. ops: dict(g='h', q=[0]), dict(g='cx', q=[0, 1]), dict(g='measure', q=[0], c=0)…"""
    return dict(type="circuit", qubits=qubits, ops=ops, **k)


def G(g: str, *q: int, **k: Any) -> Block:
    """Atajo para una operación de circuito: G('cx', 0, 1, hidden=True)."""
    return dict(g=g, q=list(q), **k)


def Hist(data: Iterable[Iterable[Any]], **k: Any) -> Block:
    return dict(type="hist", data=[list(d) for d in data], **k)


def Table(head: list[str], rows: list[list[Any]], **k: Any) -> Block:
    return dict(type="table", head=head, rows=rows, **k)


def Flow(steps: Iterable[Any], **k: Any) -> Block:
    return dict(type="flow", steps=[s if isinstance(s, dict) else dict(t=s) for s in steps], **k)


def Graph(nodes: Any, edges: Any, **k: Any) -> Block:
    return dict(type="graph", nodes=nodes, edges=edges, **k)


def A(do: str, id: str | None = None, at: str | None = None, t: float = 0, **k: Any) -> Block:
    """Acción: A('show', 'eq1', at='marca', t=0.5)."""
    d = dict(do=do, **k)
    if id is not None:
        d["id"] = id
    if at is not None:
        d["at"] = at
    if t:
        d["t"] = t
    return d


def shows(*pairs: tuple[str, str]) -> list[Block]:
    """shows(('marca', 'id'), ...) → acciones 'show' en esas marcas."""
    return [A("show", i, at=m) for m, i in pairs]


def beat(
    id: str,
    tag: Iterable[Any],
    say: str,
    scene: list[Block],
    actions: Iterable[Block] = (),
    ask: Block | None = None,
    title: str | None = None,
    **k: Any,
) -> Block:
    b = dict(
        id=id, tag=list(tag), say=" ".join(say.split()), scene=scene, actions=list(actions), **k
    )
    if title:
        b["title"] = title
    if ask:
        b["ask"] = ask
        b.setdefault("align", "top")
    return b


def choice(
    prompt: str,
    options: list[str],
    right: int,
    why: str,
    wrong: Any = None,
    hint: str | None = None,
) -> Block:
    d = dict(kind="choice", prompt=prompt, options=options, right=right, why=why)
    if wrong:
        d["wrong"] = wrong
    if hint:
        d["hint"] = hint
    return d


def numeric(
    prompt: str,
    answer: float,
    why: str,
    tol: float = 0.01,
    hint: str | None = None,
    solution: Any = None,
    unit: str | None = None,
) -> Block:
    d = dict(kind="numeric", prompt=prompt, answer=answer, why=why, tol=tol)
    for key, v in (("hint", hint), ("solution", solution), ("unit", unit)):
        if v:
            d[key] = v
    return d


def reveal(prompt: str, solution: str, button: str | None = None) -> Block:
    d = dict(kind="reveal", prompt=prompt, solution=solution)
    if button:
        d["button"] = button
    return d


def predict(prompt: str, options: list[str], after: str) -> Block:
    """Apuesta antes de ver el resultado: cualquier opción vale; no cuenta en la puntuación.
    after: lo que se dice al elegir (el resultado se revela en el paso siguiente)."""
    return dict(kind="predict", prompt=prompt, options=options, after=after)


def reflect(*prompts: str) -> Block:
    """Preguntas abiertas con cuadro de texto; las respuestas se guardan en el navegador."""
    return dict(kind="reflect", prompts=list(prompts))


def Mission(notebook: str, tasks: Iterable[tuple[int, str]], **k: Any) -> Block:
    """Tarjeta «Tu turno»: tasks = [(nivel, texto)] con nivel 1 (reproducir), 2 (modificar) o 3 (crear)."""
    return dict(
        type="mission",
        notebook=notebook,
        tasks=[dict(level=level, text=t) for level, t in tasks],
        **k,
    )


def Exercise(
    path: str,
    prompt: str,
    level: int,
    needs: str = "qiskit",
    hints: Iterable[str] = (),
    **k: Any,
) -> Block:
    """Declara un ejercicio y valida sus opciones antes de publicarlo."""
    if level not in (1, 2, 3):
        raise ValueError(f"{path}: level debe ser 1, 2 o 3, no {level!r}")
    if needs not in ("qiskit", "aer"):
        raise ValueError(f"{path}: needs debe ser 'qiskit' o 'aer', no {needs!r}")
    return dict(
        type="exercise",
        exercise=path,
        prompt=prompt,
        level=level,
        needs=needs,
        hints=list(hints),
        **k,
    )


def lesson(
    id: str,
    title: str,
    summary: str,
    goals: Iterable[str],
    beats: list[Block],
    sources: Iterable[str] = (),
    practice: Iterable[str] = (),
) -> Block:
    """sources: nombres de las guías originales de Qiskit/documentation
    (docs/guides/<nombre>) que cubre la lección.
    practice: ejercicios para hacer en tu propio entorno al terminar."""
    return dict(
        id=id,
        part="",
        section="",
        title=title,
        summary=summary,
        goals=list(goals),
        beats=beats,
        sources=list(sources),
        practice=list(practice),
        next=None,
        voice="es-PE-AlexNeural",
        rate="-4%",
    )
