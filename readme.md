# Duo

Duo is Rising's learning platform, published at `edu.rising.sh`. A catalog at
`/` lists the courses and each course lives in its own folder of `site/`. The
platform provides what all courses share: the theme, the accounts and progress,
and code execution (`/auth/*`, `/api/*`, `/run`, `/health`).

Today there is one course: **Qiskit in Spanish**, at `/qiskit/`. The course
text, narration, subtitles, questions and exercise statements are in Spanish. It
has 67 lessons in ten parts, narrated and animated, based on the IBM Quantum and
Qiskit guides, from what Qiskit is to organizations and security. Each lesson is
a sequence of steps with voice, subtitles, code that runs and questions. Some
bring a mission in a practice notebook.

Everything runs on your machine: the lessons are a static page and the notebooks
use the project's Python environment.

## Add a course

1. Create `site/<course>/` with its `index.html` and a `course.json` with
   `parts`, the list of parts, each with its `lessons` list. The catalog counts
   the lessons from that file.
2. Add an entry to `site/courses.json` with `slug` (the folder name), `title`,
   `summary` and `language`. `language` is the name of the course language that
   the catalog shows on the card, such as `"Spanish"` for the Qiskit course. A
   course in another language adds its own entry with its own `language`.
3. Link `../theme.css` and `../theme.js` from the course pages, and call the
   platform routes by their absolute path (`/api/me`, `/run`).

The platform code does not change.

## Install

You need [mise](https://mise.jdx.dev/). `mise.toml` pins the versions of Python,
uv, Node, Bun and gitleaks, and mise installs them.

```sh
mise run install
```

It installs the Python and JavaScript dependencies from their lock files, copies
KaTeX and the fonts to `site/vendor/`, and downloads Playwright's Chromium and
the original Qiskit guides.

## View the course

```sh
uv run python tools/serve.py
```

Open <http://localhost:8810/>: it is the course catalog. The Qiskit course is at
<http://localhost:8810/qiskit/>, and its home page shows the lessons by part and
your progress. A lesson opens at `qiskit/lesson.html?l=<id>`, for example
<http://localhost:8810/qiskit/lesson.html?l=p1-quickstart>. The formulas and the
fonts come from the site itself, so the page needs no internet. `tools/serve.py`
serves `site/` and also grades the code exercises of the lessons; see
[docs/exercises.md](docs/exercises.md).

## Open a practice notebook

```sh
uv run marimo edit practica/p1-quickstart.py
```

This is the command that the mission of lesson 1.4 shows. The notebooks are in
[`practica/`](practica/) and their solutions, for `tools/practica.py`, in
`practica/soluciones/`.

## Rebuild the lessons and the narration

The lessons are written in [`lessons_src/`](lessons_src/). After editing them:

```sh
uv run python tools/fetch_docs.py
uv run python lessons_src/build.py
```

The first command downloads the original Qiskit guides to `.cache/` (only the
first time). The second regenerates `site/qiskit/lessons/<id>/lesson.json` and
`site/qiskit/course.json`, and checks that every original guide has a lesson.

To also generate the audio and the timings:

```sh
uv run python lessons_src/build.py --tts
```

It needs a network (Edge TTS) and `ffprobe` (it comes with ffmpeg). Only the
clips whose text changed are synthesized.

## Check

```sh
mise run check
```

It runs `lint`, `typecheck`, `test` and `build`, and writes nothing versioned:

- `lint` checks Python with ruff, JavaScript and TypeScript with oxlint, the
  format of Markdown, JSON, YAML, JavaScript and TypeScript with oxfmt, and
  looks for secrets with gitleaks. `mise run fix` applies the safe fixes and the
  format.
- `typecheck` runs mypy in strict mode on Python and `tsc` on the Worker.
- `test` runs the notebooks with and without their solutions, grades the code
  exercises, tests the Worker, walks the site with a browser and runs the Python
  code that the lessons show.
- `build` fails if the JSON files of `site/qiskit/` or `site/qiskit/editor.js`
  do not match what `build.py` and esbuild generate. `mise run generate`
  rewrites them.

`mise run test:integration` builds the runner image and needs Docker, so `check`
does not run it. The definition of each step is in [`mise.toml`](mise.toml).

## More

[`docs/architecture.md`](docs/architecture.md) explains what each folder holds
and how a lesson gets from its source to the browser.
[`docs/exercises.md`](docs/exercises.md) describes how a code exercise is
written and graded.
