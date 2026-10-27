"""Generates a lesson's narration with Edge TTS and the per-word timings.

Usage (from the project root):
    uv run --group tools python tools/tts.py site/qiskit/lessons/p1-quickstart

Reads <lesson>/lesson.json and writes in the same folder:
    audio/<beat>.mp3          one clip per beat (and per text in "extras")
    timings.json              duration, [[name]] marks and subtitles per sentence

The [[name]] marks are written right before a word; timings.json
stores the second at which that word starts, to synchronise animations.
Before synthesis the dictionary in tools/pronunciacion.py is applied (acronyms and English
names with Spanish spelling); the subtitles keep the original text.
Only the clips whose text, voice or speed changed are regenerated.
Needs network access and ffprobe (ffmpeg).
"""

import asyncio
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import edge_tts

sys.path.insert(0, str(Path(__file__).parent))
from pronunciacion import limpiar, pronunciable

MARK = re.compile(r"\[\[(\w+)\]\]")


Words = Sequence[tuple[float, str]]


def split_marks(raw: str) -> tuple[str, dict[str, int]]:
    """Clean text and {mark: character position in the clean text}."""
    marks: dict[str, int] = {}
    clean: list[str] = []
    pos = 0
    for i, part in enumerate(MARK.split(raw)):
        if i % 2:
            if part in marks:
                raise ValueError(f"duplicate mark {part!r}")
            marks[part] = pos
        else:
            clean.append(part)
            pos += len(part)
    return "".join(clean), marks


def locator(clean: str, words: Words) -> Callable[[int], float | None]:
    """f(pos): second at which the first word at or after pos starts."""
    cursor = 0
    located: list[tuple[int, float]] = []
    for t, w in words:
        i = clean.find(w, cursor)
        if i < 0:
            continue
        located.append((i, t))
        cursor = i + len(w)
    return lambda pos: next((round(t, 3) for i, t in located if i >= pos), None)


def sentences(text: str) -> list[tuple[int, str]]:
    """Pairs (start, sentence) of the text, splitting at . ? ! and before ¿ ¡."""
    out: list[tuple[int, str]] = []
    start = 0
    for m in [*re.finditer(r"[.?!¿¡]\s+", text), None]:
        end = len(text) if m is None else m.start() if m.group()[0] in "¿¡" else m.end()
        # The signs ¿ ¡ open the next sentence.
        if text[start:end].strip():
            out.append((start, text[start:end].strip()))
        start = end
    return out


def cues(spoken: str, words: Words, shown: str) -> list[list[Any]]:
    """Subtitles: timings of the spoken text, text of the version that is shown."""
    at = locator(spoken, words)
    timed, texts = sentences(spoken), sentences(shown)
    if len(timed) != len(texts):  # should not happen: the dictionary leaves punctuation alone
        texts = timed
    return [[at(start) or 0, text] for (start, _), (_, text) in zip(timed, texts, strict=True)]


def speakable_marked(raw: str) -> str:
    """Apply the pronunciation dictionary without touching the [[name]] marks."""
    parts = MARK.split(raw)
    return "".join(f"[[{p}]]" if i % 2 else pronunciable(p) for i, p in enumerate(parts))


def duration(mp3: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
        capture_output=True,
        text=True,
        check=True,
    )
    return round(float(r.stdout), 3)


async def synth(text: str, voice: str, rate: str, path: Path) -> list[tuple[float, str]]:
    words: list[tuple[float, str]] = []
    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    with open(path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append((chunk["offset"] / 1e7, chunk["text"]))
    return words


async def main(lesson_dir: str) -> None:
    root = Path(lesson_dir)
    spec = json.loads((root / "lesson.json").read_text(encoding="utf-8"))
    out = root / "audio"
    out.mkdir(exist_ok=True)
    cache_path = root.parent.parent.parent / "content" / f"{spec['id']}.cache.json"
    cache_path.parent.mkdir(exist_ok=True)
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    voice, rate = spec["voice"], spec.get("rate", "+0%")

    clips = {b["id"]: b["say"] for b in spec["beats"]}
    clips.update(spec.get("extras", {}))

    timings: dict[str, Any] = {}
    for cid, raw in clips.items():
        shown, _ = split_marks(limpiar(raw))
        clean, marks = split_marks(speakable_marked(raw))
        key = hashlib.sha1(f"{voice}|{rate}|{clean}".encode()).hexdigest()
        mp3 = out / f"{cid}.mp3"
        old = cache.get(cid)
        if old and old["key"] == key and mp3.exists() and mp3.stat().st_size:
            words = old["words"]
        else:
            words = await synth(clean, voice, rate, mp3)
            print(f"{cid}: synthesized")
        at = locator(clean, words)
        mt = {name: at(pos) for name, pos in marks.items()}
        missing = [n for n, t in mt.items() if t is None]
        if missing:
            raise SystemExit(f"{cid}: marks without a word: {missing}")
        entry = {"key": key, "words": words}
        cache[cid] = entry
        timings[cid] = {"dur": duration(mp3), "marks": mt, "cues": cues(clean, words, shown)}
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    (root / "timings.json").write_text(
        json.dumps(timings, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"done: {len(timings)} clips")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
