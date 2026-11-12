# Architecture

Rising is a static site (`site/`) with a course catalog and a Worker, `duo`,
that serves what the courses share: accounts, progress and code execution. This
document says what each folder holds and where a request goes.

## Folders

| Folder         | Contents                                                                                            |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `app/`         | The shell: catalog, course path pages and privacy page, as a React app prerendered into `site/`.    |
| `site/`        | The static site: the shell, what the courses share and one folder per course. [Detail](#site)       |
| `lessons_src/` | The lessons of each course as Python code, one folder per course, and the program that builds them. |
| `exercises/`   | The code exercises: starter code, solution and cases of each.                                       |
| `qgcheck/`     | The exercise grader: runs a learner's code and returns the result of each case.                     |
| `runner/`      | The runner image (`server.py`, `sandbox.py`) and the Worker (`worker/`).                            |
| `editor/`      | The package that bundles `site/player/editor.js` and copies KaTeX and Pyodide to `site/vendor/`.    |
| `content/`     | The speech synthesis cache.                                                                         |
| `tools/`       | Helper programs: original guides, narration, checks, local server, dashboard and browser tools.     |
| `tests/`       | Browser tests, exercise tests, runner tests and dashboard tests.                                    |
| `stubs/`       | Types of `qiskit` and `qiskit_aer` for mypy.                                                        |

Each part has its own document:

| Part                             | Document                       |
| -------------------------------- | ------------------------------ |
| `lessons_src/`                   | [lessons.md](lessons.md)       |
| `exercises/`, `qgcheck/`         | [exercises.md](exercises.md)   |
| `runner/` (image)                | [runner.md](runner.md)         |
| `runner/worker/` (accounts)      | [accounts.md](accounts.md)     |
| `runner/worker/` (limits, spend) | [protection.md](protection.md) |
| Theme of `site/`                 | [design.md](design.md)         |
| Publishing                       | [deploy.md](deploy.md)         |

## `app/`

The shell is a Vite and React 19 app. `mise run generate:app` builds it and
prerenders every page into `site/`, where Git ignores the result:

- `/` is the catalog: one card per course, with its outcome, the progress if the
  learner started and one button that opens the next lesson.
- `/<slug>/` is the path page of a course: the outcome, current project
  milestone, units, path progress and optional guide links. It also has the
  review card and, if the course has one, the project track.
- `/<slug>/repaso/` is the drill session of a course ([drills.md](drills.md)).
  Its code loads in a chunk of its own, after the page, so the budget below does
  not count it.
- `/privacidad.html` says what is stored
  ([accounts.md](accounts.md#on-the-site)).

Each page is a static HTML file with its content drawn, so it paints before any
script runs. The page's data sits in a `<script type="application/json">` and
`entry-client.tsx` hydrates the page with it. The server draws an empty state;
once hydrated, the page reads `localStorage` and draws the learner's progress.

The routes come from `site/courses.json`, so a new course adds no code to
`app/`. Every page loads `assets/index-<hash>.js` and the shared `theme.js` and
`account.js`, 84 KB of gzipped JavaScript in all. `tests/budget_test.ts` fails
above 100 KB.

| Path                     | Contents                                                       |
| ------------------------ | -------------------------------------------------------------- |
| `app/scripts/build.ts`   | The build: client and server bundles, prerender, `sw.js`.      |
| `app/scripts/sw.js`      | The template of the service worker.                            |
| `app/scripts/icons.ts`   | Draws `site/icons/*.png` (`bun app/scripts/icons.ts`).         |
| `app/src/model.ts`       | The types of `courses.json`, `course.json` and `project.json`. |
| `app/src/path.ts`        | Which lesson is done, current or locked, and what is next.     |
| `app/src/store.ts`       | Reads progress from `localStorage` for the components.         |
| `app/src/components/`    | The pages.                                                     |
| `app/src/styles/app.css` | The shell styles ([design.md](design.md)).                     |

## `site/`

The root holds the shell and what the courses share:

- `index.html`, `privacidad.html`, `<slug>/index.html`,
  `<slug>/repaso/index.html`, `assets/` and `sw.js` are the output of `app/`.
- `courses.json` has one entry per course: `slug`, `title`, `outcome` (the
  sentence the catalog and the path page show), and optionally `source`
  (`label`, `url`, `license`) and `note`.
- `theme.css` and `theme.ts` are the theme of the shell and of the player
  ([design.md](design.md)). The labels of the theme control follow the page's
  `lang`.
- `progress.ts` is the one place that knows the `localStorage` keys, shared by
  the shell, the player and the account.
- `account.ts` is the account menu ([accounts.md](accounts.md#on-the-site)).
- `manifest.webmanifest` and `icons/` make the site installable. `sw.js` is the
  service worker.
- `fonts/` is Inter, the one face of every page.
- `vendor/` is KaTeX and Pyodide, copied from `editor/node_modules` by
  `editor/vendor.ts` and `editor/vendor-pyodide.ts`. Git ignores it;
  `mise run install` and `mise run deploy` generate it. Only the exercise pages
  of a [browser course](exercises.md#a-course-that-grades-in-the-browser) load
  Pyodide. No page requests anything from another site except the Turnstile
  script, which `exercise.ts` downloads from Cloudflare when the runner requires
  it.
- The page scripts are written in TypeScript. `mise run generate:scripts`
  bundles them with `bun build` into `theme.js`, `account.js`,
  `player/engine.js`, `player/editor.js` and `player/pyodide-worker.js`, which
  the pages load and Git ignores. The `install`, `serve`, `deploy` and `test:ui`
  tasks run it. `tsconfig.json` types them and `globals.d.ts` declares what they
  share through `window`.

`player/` is the lesson player, the same for every course. A lesson page loads
it with `../player/`:

- `engine.ts` loads `lesson.json` and plays it. It imports `blocks.ts`, which
  draws the blocks, `exercise.ts`, the exercise block, and `sfx.ts`, the sounds.
  `lesson.ts` holds the types of `lesson.json` and of the contract between the
  engine and the blocks.
- `app.css` styles the player.
- `editor.js` is the CodeMirror 6 editor of the exercises, bundled from
  `editor/src/index.ts` ([exercises.md](exercises.md#rebuild-the-editor)).

A course is a folder `site/<slug>/` and a line in `courses.json`. It links the
theme and `vendor/` with `../`, and calls the platform routes by their absolute
path:

- `course.json` is the generated index of path units, lessons and minutes. It
  may also have `guides`, which are lessons outside the path and its progress
  count. The path page draws one unit per part and one node per path lesson.
- `project.json` is optional: the milestones of a project track, each tied to a
  part, lesson and exercise. A course without it shows no track.
- `index.html` is the path page, generated from the two files above.
- `lesson.html` loads `../player/engine.js` and `../player/app.css`. KaTeX draws
  the formulas and the page loads it with `defer`, before its own scripts.
- `lessons/<id>/` holds `lesson.json`, `timings.json` and `audio/<step>.mp3`,
  all generated ([lessons.md](lessons.md)).

## Progress in the browser

`progress.ts` defines the keys of `localStorage`. A course writes under its own
slug: `<slug>:done`, `<slug>:pos:<lesson>`, `<slug>:heard:<lesson>`,
`<slug>:exercise:<lesson>/<name>`, `<slug>:hitos`, `<slug>:repaso` (the answers
of the drill sessions) and so on. What belongs to no course uses `rising:`:

| Key               | Contents                                                  |
| ----------------- | --------------------------------------------------------- |
| `rising:theme`    | `light` or `dark` ([design.md](design.md#mode)).          |
| `rising:speed`    | The playback speed of the player.                         |
| `rising:mute`     | Whether the player's sounds are off.                      |
| `rising:cuenta`   | The id of the account this browser is signed in to.       |
| `rising:xp`       | XP earned by day, `{"2026-01-31": 20}`.                   |
| `rising:last`     | The course whose lesson the learner opened last.          |
| `rising:xpq:<id>` | The XP posts that account has not received, or `anon`.    |
| `rising:xpsent`   | Set once the XP earned before signing in has been queued. |
| `rising:tally`    | The account's streak and XP, as the last answers said.    |
| `rising:amigos`   | The numbers of the friends' labels, `Amigo 1`, `Amigo 2`. |
| `rising:migrated` | Set once the keys written by earlier versions have moved. |

The first lesson a learner completes earns 10 XP. The streak counts the days in
a row with XP, ending today or yesterday, and the header of the path page shows
it with the XP of today. Both live only in the browser. A drill session adds its
XP to the same record.

Earlier versions wrote every course under `qiskit:`. On its first load,
`account.ts` splits `qiskit:done` and the keys of each lesson between the
courses that own them, moves `qiskit:theme`, `qiskit:speed`, `qiskit:mute` and
`qiskit:cuenta` to `rising:`, and sets `rising:migrated`. A lesson id belongs to
one course. The player moves the keys of a lesson when it opens it. Both leave
the keys that already exist in place.

## Offline

`sw.js` is the service worker. It is installed by the shell pages, and it caches
the shell pages, `theme.js`, `account.js`, `manifest.webmanifest`, the hashed
files in `assets/` (the script, the styles and the Inter font), `courses.json`
and the `course.json` and `items.json` of each course, with the session page and
its chunk. The pages and the course indexes load from the network first or
answer from the cache, so a deploy shows at once and the app launches with no
connection. Hashed files answer from the cache.

The service worker leaves alone the lesson page, the lesson files with their
audio, `/run`, `/health`, `/auth/*` and `/api/*`. A lesson needs the network.

`mise run test:walkthrough` plays one learner through the Qiskit course in a
browser: it finishes every lesson and reads back the path page after each step.
`mise run test:ui` runs `tests/shell_test.ts` (the path from the catalog to a
lesson, the key migration, the streak and the offline launch),
`tests/session_test.ts` (a drill session of every kind) and
`tests/budget_test.ts`.

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
`/run` with `qgcheck`, with no accounts and no limits (a course that grades in
the browser needs neither) ([exercises.md](exercises.md#where-the-code-runs)).
