# Duo

Duo is a platform of courses for learning by doing, published at
`edu.rising.sh`. A catalog at `/` lists the courses and each course is a folder
of `site/`. The platform provides what the courses share: the theme, the
accounts with their progress and code execution in the browser.

The only course is **Qiskit**, at `/qiskit/`, in Spanish: narrated lessons with
animations, code exercises that are checked on the page, practice notebooks and
a project that grows part by part. The lessons are a static page; the notebooks
use the project's Python environment.

## Install

You need [mise](https://mise.jdx.dev/). `mise.toml` pins the versions of Python,
uv, Node, Bun and gitleaks, and mise installs them.

```sh
mise run install
```

It installs the Python and JavaScript dependencies from their lock files, copies
KaTeX and the fonts to `site/vendor/`, bundles the scripts (see
[View the course](#view-the-course)) and downloads Playwright's Chromium and the
original Qiskit guides.

## View the course

```sh
mise run serve
```

The browser scripts are written in TypeScript (`site/theme.ts`,
`site/qiskit/*.ts` and `editor/src/`). `mise run generate:scripts` bundles them
with `bun build` into `site/theme.js` and
`site/qiskit/{account,notebooks,engine,editor}.js`, which the pages load and Git
ignores; `mise run serve` runs it before serving.

Open <http://localhost:8810/>: it is the catalog. The Qiskit course is at
<http://localhost:8810/qiskit/>, and a lesson opens at
`qiskit/lesson.html?l=<id>`, for example
<http://localhost:8810/qiskit/lesson.html?l=p1-quickstart>. The page needs no
internet. `tools/serve.py` serves `site/` and grades the code exercises on your
machine, without accounts.

## Open a practice notebook

```sh
uv run marimo edit practica/p1-quickstart.py
```

It is the notebook of the mission of lesson `p1-quickstart`. The notebooks are
in [`practica/`](practica/).

## Add a course

1. Create `site/<course>/` with its `index.html` and a `course.json` with
   `parts`, the list of parts, each with its `lessons` list. The catalog counts
   the lessons from that file.
2. Add an entry to `site/courses.json` with `slug` (the folder name), `title`,
   `summary` and `language`.
3. Link `../theme.css` and `../theme.js` from the course pages, and call the
   platform routes by their absolute path (`/api/me`, `/run`).

The platform code does not change.

## Check

```sh
mise run check
```

It runs `lint`, `typecheck`, `test` and `build`, and writes nothing versioned.
`mise run fix` applies the safe fixes and the format, and `mise run generate`
rewrites the generated files that `build` finds out of date.
`mise run test:integration` builds the runner image and needs Docker, so `check`
does not run it. The definition of each step is in [`mise.toml`](mise.toml).

## Deploy

The site is published as a Cloudflare Worker with a container that runs code.
[docs/deploy.md](docs/deploy.md) takes whoever forks the repository step by step
to their own copy.

## More

[docs/readme.md](docs/readme.md) is the index of the documentation.
