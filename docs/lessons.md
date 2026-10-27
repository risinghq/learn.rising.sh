# Lessons and notebooks

A lesson of the Qiskit course is a sequence of steps with voice, subtitles,
animations, code and questions. It is written in Python (`lessons_src/`), turned
into JSON and played by `engine.ts`. Practice is marimo notebooks (`practica/`)
and code exercises ([exercises.md](exercises.md)).

## From the source to the browser

```text
plan.py + parte*.py -> build.py -> lesson.json (and course.json)
lesson.json -> tts.py -> audio/<step>.mp3 + timings.json
lesson.json + timings.json + audio -> engine.ts
```

- `plan.py` defines `PARTS`: the ten parts, the order of the lessons and which
  original guides each one covers. A guide appears in exactly one lesson.
- `parte1.py` to `parte10.py` define `LESSONS`, the list of lessons of each
  part, with the functions of `lib.py`: `lesson()`, `beat()`, the blocks
  (`Code`, `Out`, `Circ`, `Hist`…), the actions (`A`) and the questions
  (`choice`, `numeric`, `reveal`, `predict`, `reflect`).
- `build.py` joins the plan with the lessons and writes the JSON of
  `site/qiskit/`. It numbers the sections following `plan.PARTS`, adds to each
  lesson the link to its original guides and completes each `Exercise` block
  with what the site can show from `exercises/`. `course.json` adds up the
  minutes: the duration from `timings.json` if it exists, or an estimate by
  words if not, plus 45 seconds per question. First it checks that every guide
  in the Qiskit/documentation index is in the plan, that no `[[name]]` mark
  repeats in a narration and that every action points at a mark and an object
  that exist. It fails if a lesson in the plan has no module or if a module
  defines a lesson that the plan does not mention.
- `tts.py` reads `lesson.json`. For each step it applies `pronunciacion.py` to
  the `say` text, synthesizes `audio/<step>.mp3` with Edge TTS and measures its
  duration with `ffprobe`. `timings.json` holds per step `dur` (seconds),
  `marks` (the second at which the word after each `[[mark]]` starts) and `cues`
  (the subtitles with their start second). `content/<id>.cache.json` holds per
  clip the hash of what was said and the time of each word, so a clip that did
  not change is not synthesized again.
- `engine.ts` loads `lesson.json` and `timings.json`, plays the audio of each
  step and fires each action of `actions` at the second of its mark. The
  subtitles come from `cues`. `?beat=N` shows the final state of step N without
  audio.

To regenerate after editing a lesson:

```sh
uv run python tools/fetch_docs.py
uv run python lessons_src/build.py
uv run python lessons_src/build.py --tts
```

`fetch_docs.py` downloads the original guides to `.cache/qiskit-docs`, at the
version `tools/qiskit-docs.commit` pins (only needed the first time). `--tts`
needs a network (Edge TTS) and `ffprobe`, which comes with ffmpeg. To update the
guides, change the hash in `qiskit-docs.commit`, run `fetch_docs.py` and fix
`plan.py` until `build.py` passes.

## Programs in `tools/`

| Program                                              | Function                                                                                                                            |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Downloads `docs/guides` of Qiskit/documentation to `.cache/qiskit-docs`.                                                            |
| `extract.py`                                         | Converts those guides to plain text in `.cache/qiskit-docs/text`.                                                                   |
| `tts.py`                                             | Synthesizes the narration of a lesson and writes `timings.json`.                                                                    |
| `pronunciacion.py`                                   | Dictionary that rewrites English acronyms and names so the voice reads them well.                                                   |
| `verify.py`                                          | Runs the Python of the lessons, except `norun`, and compares the `Out(…, check=True)`.                                              |
| `practica.py`                                        | Runs each notebook with and without solutions. It also tests `mo.ui.slider`/`number` at minimum and maximum. A runtime error fails. |
| `exercises.py`                                       | Runs the solution and the starter code of each exercise with `qgcheck` and checks its `needs`.                                      |
| `serve.py`                                           | Serves `site/` locally and answers `POST /run`.                                                                                     |
| `dashboard.ts`                                       | The operator dashboard ([accounts.md](accounts.md#where-learners-get-stuck)).                                                       |
| `playtest.ts`, `seektest.ts`, `shot.ts`, `review.ts` | Playwright tests and screenshots on the course served on port 8810.                                                                 |

The `.ts` programs run with Bun: `bun tools/shot.ts <lesson> <beats>`.

## The cycle of a lesson

Each lesson leads the learner to act and to reflect, not only to watch:

1. **Predict.** Before seeing a result, the learner bets an answer (`predict`).
   The bet does not change afterwards.
2. **Watch.** The narrated animation.
3. **Do.** A mission ([`Mission`](#missions-and-notebooks)) with the lesson's
   notebook, or a [code exercise](exercises.md) that is checked on the page.
4. **Reflect.** Open questions (`reflect`). The text is saved in the browser
   (`qiskit:reflect`) and shows when the learner returns.
5. **Recap.** The summary of the lesson.

## Missions and notebooks

A mission names a notebook in `practica/` and its tasks, each with a level: 🟢 1
reproduce, 🟡 2 modify, 🔴 3 create. Each task has its check in the notebook. A
[code exercise](exercises.md) uses the same three levels in its `level` field.

The notebooks are the `.py` files of `practica/` that contain `marimo.App(`.
They open with `uv run marimo edit practica/<id>.py`. Qiskit does not run in the
browser, so the notebooks run on your machine, in the project's Python
environment.

marimo and not Jupyter because it is reactive: when you change something
everything recomputes, so the checks say ✅ or ❌ at once, and the sliders suit
exploring parameters. Its files are plain `.py`, easy to version and to check
with `tools/practica.py`. The IBM guides and the community use Jupyter, so a
mission in Part I teaches how to convert between the two formats with
`marimo convert`.

A notebook can import a module from its folder (`proyecto/ising.py`) because
`tools/practica.py` puts that folder on `sys.path`.
`practica/soluciones/<notebook>.json` (with `__` instead of `/` for notebooks in
subfolders) holds the (text, replacement) pairs that `tools/practica.py` applies
to check that all the verifications give ✅.

## The spin chain project

One experiment grows part by part: the magnetization of an Ising spin chain
after a sudden change of the field. There is one milestone per part, in
`practica/proyecto/hito<N>.py` (N from 1 to 10), and a shared module,
`practica/proyecto/ising.py`. The titles and descriptions of the milestones are
in `HITOS`, in `site/qiskit/index.html`, which shows them on the course home
page with their state (saved in `qiskit:hitos`). The milestones that run on a
real QPU ask for an IBM Quantum account.

## Spaced review

The course home page proposes each day 3 questions from the completed lessons
(the `choice` and `numeric` ones), spaced 1, 3, 7 and 21 days. A question that
is missed comes back the next day. The state is in `qiskit:repaso`.
