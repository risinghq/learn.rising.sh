# Lessons and notebooks

A lesson is a sequence of steps with voice, subtitles, animations, code and
questions. It is written in Python (`lessons_src/<course>/`), turned into JSON
and played by `site/player/engine.ts`, the same player for every course. The
Qiskit course also has marimo notebooks for practice (`practica/`). Every course
has code exercises ([exercises.md](exercises.md)).

## From the source to the browser

```text
lessons_src/<course>/plan.py + parte*.py -> build.py <course> -> lesson.json (and course.json)
lesson.json -> tts.py -> audio/<step>.mp3 + timings.json
lesson.json + timings.json + audio -> engine.ts
```

- A course is `site/<slug>/` and its source `lessons_src/<slug>/`, with the
  dashes of the slug written as underscores (`computational_physics`). See
  [Add a course](#add-a-course).
- `plan.py` defines `PARTS`: the parts (`n`, `title`, `desc`), the order of
  their lessons, and for each lesson `(id, title)`. A lesson id belongs to one
  course. The Qiskit plan adds a third element, the original guides that the
  lesson covers; a guide appears in exactly one lesson.
- `parte*.py` define `LESSONS`, the list of lessons of each part, with the
  functions of `lessons_src/lib.py`: `lesson()`, `beat()`, the blocks (`Code`,
  `Out`, `Plot`, `Circ`, `Hist`…), the actions (`A`) and the questions
  (`choice`, `numeric`, `reveal`, `predict`, `reflect`). The blocks `Circ` and
  `Hist` draw Qiskit circuits and counts; a course that does not use Qiskit
  leaves them out.
- `hooks.py` is optional. If a course has it, `build.py` calls `check()`, which
  fails the build with a message, and `references(sources)`, which returns lines
  to add to the lesson's practice list. Only the Qiskit course has one: it
  checks that every guide of the Qiskit/documentation index is in the plan and
  links each lesson to its guides.
- `build.py <course>` joins the plan with the lessons and writes the JSON of
  `site/<course>/`. It numbers the sections following `plan.PARTS` and completes
  each `Exercise` block with what the site can show from `exercises/`.
  `course.json` adds up the minutes: the duration from `timings.json` if it
  exists, or an estimate by words if not, plus 45 seconds per question. It
  checks that no `[[name]]` mark repeats in a narration and that every action
  points at a mark and an object that exist. It fails if a lesson in the plan
  has no module, if a module defines a lesson that the plan does not mention, or
  if a lesson id is already in another course.
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

To regenerate after editing a lesson of the computational physics course:

```sh
uv run python lessons_src/build.py computational-physics
uv run python lessons_src/build.py computational-physics --tts
```

For the Qiskit course:

```sh
uv run python tools/fetch_docs.py
uv run python lessons_src/build.py qiskit
uv run python lessons_src/build.py qiskit --tts
```

`mise run generate:lessons` builds every course. `--check` writes nothing and
fails if the JSON on disk differs from what the source generates. `--tts` needs
a network (Edge TTS) and `ffprobe`, which comes with ffmpeg; Edge TTS can refuse
requests for a while after many in a row, and running the command again
continues where it stopped.

`fetch_docs.py` downloads the original guides to `.cache/qiskit-docs`, at the
version `tools/qiskit-docs.commit` pins (only needed the first time). To update
the guides, change the hash in `qiskit-docs.commit`, run `fetch_docs.py` and fix
the Qiskit `plan.py` until `build.py qiskit` passes.

## Add a course

The platform code does not change.

1. Create `lessons_src/<slug>/` with a `plan.py` and at least one `parte*.py`.
2. Create `site/<slug>/` with a copy of the `index.html` and `lesson.html` of an
   existing course. They link the shared theme, account menu and player, and
   call the platform routes by their absolute path (`/api/me`, `/run`).
3. Add an entry to `site/courses.json` with `slug` (the folder name), `title`,
   `summary` and `language`. `language` is the name of the course language that
   the catalog shows on the card, such as `"Spanish"`. The catalog counts the
   lessons from `site/<slug>/course.json`, which `build.py` writes.
4. Add the course to `generate:lessons` and `build:lessons` in `mise.toml`, then
   run `uv run python lessons_src/build.py <slug>`.

## Charts

`Plot` draws axes and curves. A curve is a formula in `x` (`expr`) or a list of
`[x, y]` points (`pts`) that the player joins with straight lines in the order
given, so it can loop like an orbit. A lesson that teaches a simulation computes
its `pts` in the lesson source with the same method the lesson explains, and
`A("curve", id, at=, i=)` draws curve `i` as the narration reaches its mark.

## Programs in `tools/`

| Program                                              | Function                                                                                                                            |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Downloads `docs/guides` of Qiskit/documentation to `.cache/qiskit-docs`.                                                            |
| `extract.py`                                         | Converts those guides to plain text in `.cache/qiskit-docs/text`.                                                                   |
| `tts.py`                                             | Synthesizes the narration of a lesson and writes `timings.json`.                                                                    |
| `pronunciacion.py`                                   | Dictionary that rewrites English acronyms and names so the voice reads them well.                                                   |
| `verify.py`                                          | Runs the Python of the lessons of every course, except `norun`, and compares the `Out(…, check=True)`.                              |
| `practica.py`                                        | Runs each notebook with and without solutions. It also tests `mo.ui.slider`/`number` at minimum and maximum. A runtime error fails. |
| `exercises.py`                                       | Runs the solution and the starter code of each exercise with `qgcheck` and checks its `needs`.                                      |
| `serve.py`                                           | Serves `site/` locally and answers `POST /run`.                                                                                     |
| `dashboard.ts`                                       | The operator dashboard ([accounts.md](accounts.md#where-learners-get-stuck)).                                                       |
| `playtest.ts`, `seektest.ts`, `shot.ts`, `review.ts` | Playwright tests and screenshots of a lesson served on port 8810. The lesson id says which course opens.                            |

The `.ts` programs run with Bun: `bun tools/shot.ts <lesson> <beats>`, for
example `bun tools/shot.ts f1-euler-leapfrog 4,5 laptop`.
`bun tools/review.ts --course computational-physics` reviews every lesson of a
course.

## The cycle of a lesson

Each lesson leads the learner to act and to reflect, not only to watch:

1. **Predict.** Before seeing a result, the learner bets an answer (`predict`).
   The bet does not change afterwards.
2. **Watch.** The narrated animation.
3. **Do.** A [code exercise](exercises.md) that is checked on the page or, in
   the Qiskit course, a mission ([`Mission`](#missions-and-notebooks)) with the
   lesson's notebook.
4. **Reflect.** Open questions (`reflect`). The text is saved in the browser
   (`qiskit:reflect`) and shows when the learner returns.
5. **Recap.** The summary of the lesson.

## Missions and notebooks

Only the Qiskit course has them. A mission names a notebook in `practica/` and
its tasks, each with a level: 🟢 1 reproduce, 🟡 2 modify, 🔴 3 create. Each
task has its check in the notebook. A [code exercise](exercises.md) uses the
same three levels in its `level` field.

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

One experiment grows part by part in the Qiskit course: the magnetization of an
Ising spin chain after a sudden change of the field. There is one milestone per
part, in `practica/proyecto/hito<N>.py` (N from 1 to 10), and a shared module,
`practica/proyecto/ising.py`. The titles and descriptions of the milestones are
in `HITOS`, in `site/qiskit/index.html`, which shows them on the course home
page with their state (saved in `qiskit:hitos`). The milestones that run on a
real QPU ask for an IBM Quantum account.

## Spaced review

The Qiskit course home page proposes each day 3 questions from the completed
lessons (the `choice` and `numeric` ones), spaced 1, 3, 7 and 21 days. A
question that is missed comes back the next day. The state is in
`qiskit:repaso`.
