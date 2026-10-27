# Architecture

Duo is a static site (`site/`) with a course catalog and a Worker that serves
what the courses share: accounts, progress and code execution. This document
says what each folder holds and where a request goes.

## Folders

| Folder         | Contents                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------- |
| `site/`        | The static site: the catalog, the shared theme and one folder per course. [Detail](#site)         |
| `lessons_src/` | The lessons of the Qiskit course as Python code and the program that turns them into JSON.        |
| `practica/`    | The marimo notebooks of the missions, the project and their solutions.                            |
| `exercises/`   | The code exercises: starter code, solution and cases of each.                                     |
| `qgcheck/`     | The exercise grader: runs a learner's code and returns the result of each case.                   |
| `runner/`      | The runner image (`server.py`, `sandbox.py`) and the Worker (`worker/`).                          |
| `editor/`      | The package that builds `site/qiskit/editor.js` and copies KaTeX and the fonts to `site/vendor/`. |
| `content/`     | The speech synthesis cache.                                                                       |
| `tools/`       | Helper programs: original guides, narration, checks, local server and dashboard.                  |
| `tests/`       | Browser tests, exercise tests, runner tests and dashboard tests.                                  |
| `stubs/`       | Types of `qiskit` and `qiskit_aer` for mypy.                                                      |

Each part has its own document:

| Part                             | Document                       |
| -------------------------------- | ------------------------------ |
| `lessons_src/`, `practica/`      | [lessons.md](lessons.md)       |
| `exercises/`, `qgcheck/`         | [exercises.md](exercises.md)   |
| `runner/` (image)                | [runner.md](runner.md)         |
| `runner/worker/` (accounts)      | [accounts.md](accounts.md)     |
| `runner/worker/` (limits, spend) | [protection.md](protection.md) |
| Theme of `site/`                 | [design.md](design.md)         |
| Publishing                       | [deploy.md](deploy.md)         |

## `site/`

The root holds the catalog and what the courses share:

- `index.html` and `catalog.css` are the catalog, in English. It reads
  `courses.json`, which has one entry per course (`slug`, `title`, `summary`,
  `language`), and from each `<slug>/course.json` the number of lessons. It
  draws one card per course with a link to `<slug>/`.
- `theme.css` and `theme.js` are the theme of the catalog and of the courses
  ([design.md](design.md)). The labels of the theme control follow the page's
  `lang`.
- `vendor/` is KaTeX and the two fonts, copied from `editor/node_modules` by
  `editor/vendor.js`. Git ignores it; `mise run install` and `mise run deploy`
  generate it. No page requests anything from another site except the Turnstile
  script, which `exercise.js` downloads from Cloudflare when the runner requires
  it.

`qiskit/` is the Qiskit course. Its pages link the theme and `vendor/` with
`../`, and call the platform routes by their absolute path:

- `index.html` is the course home page, styled by `index.css`. It reads
  `course.json` and requests the `lesson.json` of the completed lessons to build
  the review.
- `lesson.html` loads `engine.js`, the player, styled by `app.css`. `blocks.js`
  draws the course's own blocks, `exercise.js` the exercise block and `sfx.js`
  the sounds. KaTeX draws the formulas and both pages load it with `defer`,
  before their own scripts.
- `account.js` is the account menu and `privacidad.html` the page that says what
  is stored ([accounts.md](accounts.md#on-the-site)).
- `editor.js` is the CodeMirror 6 editor of the exercises, bundled from
  `editor/` ([exercises.md](exercises.md#rebuild-the-editor)).
- `notebooks.js` writes the "how to run the notebooks" line that goes with each
  `marimo` command.
- `lessons/<id>/` holds `lesson.json`, `timings.json` and `audio/<step>.mp3`.
- `course.json` is the index: parts, lessons, minutes and missions.

## A request

A single Worker, `duo`, serves `site/` as static files and answers four routes
before the files:

| Route     | Who answers it                                                                                                          |
| --------- | ----------------------------------------------------------------------------------------------------------------------- |
| `/run`    | The Worker checks the request ([protection.md](protection.md)) and passes it to the container ([runner.md](runner.md)). |
| `/auth/*` | Sign-in ([accounts.md](accounts.md#sign-in)).                                                                           |
| `/api/*`  | The account and its progress ([accounts.md](accounts.md#progress)).                                                     |
| `/health` | The Worker, without touching the container.                                                                             |

On your machine there is no Worker: `tools/serve.py` serves `site/` and answers
`/run` with `qgcheck`, with no accounts and no limits
([exercises.md](exercises.md#where-the-code-runs)).
