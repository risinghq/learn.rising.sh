# Architecture

Duo is a static site (`site/`) with a course catalog and a Worker that serves
what the courses share: accounts, progress and code execution. This document
says what each folder holds and where a request goes.

## Folders

| Folder         | Contents                                                                                            |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `site/`        | The static site: the catalog, what the courses share and one folder per course. [Detail](#site)     |
| `lessons_src/` | The lessons of each course as Python code, one folder per course, and the program that builds them. |
| `practica/`    | The marimo notebooks of the missions, the project and their solutions.                              |
| `exercises/`   | The code exercises: starter code, solution and cases of each.                                       |
| `qgcheck/`     | The exercise grader: runs a learner's code and returns the result of each case.                     |
| `runner/`      | The runner image (`server.py`, `sandbox.py`) and the Worker (`worker/`).                            |
| `editor/`      | The package that bundles `site/player/editor.js` and copies KaTeX and the fonts to `site/vendor/`.  |
| `content/`     | The speech synthesis cache.                                                                         |
| `tools/`       | Helper programs: original guides, narration, checks, local server, dashboard and browser tools.     |
| `tests/`       | Browser tests, exercise tests, runner tests and dashboard tests.                                    |
| `stubs/`       | Types of `qiskit` and `qiskit_aer` for mypy.                                                        |

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
- `theme.css` and `theme.ts` are the theme of the catalog and of the courses
  ([design.md](design.md)). The labels of the theme control follow the page's
  `lang`.
- `course.css` and `course-home.ts` are the course home page: the styles, and
  `QGHome.renderParts`, which draws the card of each part with the progress of
  its lessons.
- `account.ts` is the account menu and `privacidad.html` the page that says what
  is stored ([accounts.md](accounts.md#on-the-site)).
- `vendor/` is KaTeX and the two fonts, copied from `editor/node_modules` by
  `editor/vendor.ts`. Git ignores it; `mise run install` and `mise run deploy`
  generate it. No page requests anything from another site except the Turnstile
  script, which `exercise.ts` downloads from Cloudflare when the runner requires
  it.
- The page scripts are written in TypeScript. `mise run generate:scripts`
  bundles them with `bun build` into `theme.js`, `account.js`, `course-home.js`,
  `player/engine.js`, `player/editor.js` and `qiskit/notebooks.js`, which the
  pages load and Git ignores. The `install`, `serve`, `deploy` and `test:ui`
  tasks run it. `tsconfig.json` types them and `globals.d.ts` declares what they
  share through `window`.

`player/` is the lesson player, the same for every course. A course page loads
it with `../player/`:

- `engine.ts` loads `lesson.json` and plays it. It imports `blocks.ts`, which
  draws the blocks, `exercise.ts`, the exercise block, and `sfx.ts`, the sounds.
  `lesson.ts` holds the types of `lesson.json` and of the contract between the
  engine and the blocks.
- `app.css` styles the player.
- `editor.js` is the CodeMirror 6 editor of the exercises, bundled from
  `editor/src/index.ts` ([exercises.md](exercises.md#rebuild-the-editor)).

A course is a folder `site/<slug>/`. It links the theme and `vendor/` with
`../`, and calls the platform routes by their absolute path:

- `course.json` is the index, generated: parts, lessons, minutes and missions.
- `index.html` is the course home page. It links `../course.css` and reads
  `course.json`.
- `lesson.html` loads `../player/engine.js` and `../player/app.css`. KaTeX draws
  the formulas and both pages load it with `defer`, before their own scripts.
- `lessons/<id>/` holds `lesson.json`, `timings.json` and `audio/<step>.mp3`,
  all generated ([lessons.md](lessons.md)).

A course adds its own files beside those. `qiskit/` has `index.css`, for its
home page, and `notebooks.ts`, which writes the "how to run the notebooks" line
that goes with each `marimo` command. `computational-physics/` has none.

Every course stores its progress under the `qiskit:` keys of `localStorage`
(`qiskit:done`, `qiskit:pos:<id>`, …) and on the account, by lesson id. For that
reason a lesson id belongs to one course, and a course home page counts only its
own lessons. `mise run test:walkthrough` plays one learner through that state in
a browser: it finishes every lesson of the Qiskit course and reads back the home
page after each step. `mise run test` does not run it, because it takes over a
minute beside the other suites.

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
