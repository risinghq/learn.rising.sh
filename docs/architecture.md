# Architecture

Duo is a static site (`site/`) with a course catalog and a Worker that serves
what the courses share. The Qiskit course plays lessons described in JSON. The
lessons are written in Python, the audio is synthesized separately and the
practice notebooks are marimo files. This document says what each folder owns
and how a lesson travels.

## Who owns what

| Folder         | Contents                                                                                                                                                                    |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lessons_src/` | The lessons as Python code and the program that turns them into JSON.                                                                                                       |
| `tools/`       | Helper programs: original guides, narration, checks and browser tests.                                                                                                      |
| `site/`        | The static site: the catalog, the shared theme and one folder per course, with its home page, its lesson player and the data they read.                                     |
| `tests/`       | Browser tests (`theme_test.py`, `proyecto_test.py`, `exercise_ui_test.py`, `account_ui_test.py`), exercise tests (`exercises_test.py`) and runner tests (`runner_test.py`). |
| `practica/`    | The marimo notebooks of the missions and their solutions.                                                                                                                   |
| `exercises/`   | The code exercises: starter code, solution and cases of each.                                                                                                               |
| `editor/`      | The package that builds `site/qiskit/editor.js` and copies KaTeX and the fonts to `site/vendor/`.                                                                           |
| `qgcheck/`     | The exercise grader: reads `exercises/`, runs a learner's code and returns the result of each case.                                                                         |
| `content/`     | The speech synthesis cache.                                                                                                                                                 |
| `runner/`      | The learner code runner: image, `/run` server and Worker. [runner.md](runner.md)                                                                                            |

### `lessons_src/`

- `plan.py` defines `PARTS`: the ten parts, the order of the lessons and which
  original guides each one covers. A guide appears in exactly one lesson.
- `parte1.py` to `parte10.py` define `LESSONS`, the list of lessons of each
  part, with the functions of `lib.py`: `lesson()`, `beat()`, the blocks
  (`Code`, `Out`, `Circ`, `Hist`…), the actions (`A`) and the questions
  (`choice`, `numeric`, `reveal`, `predict`, `reflect`).
- `build.py` joins the plan with the lessons and writes the JSON of
  `site/qiskit/`. First it checks that every guide in the Qiskit/documentation
  index is in the plan, that no `[[name]]` mark repeats in a narration and that
  every action points at a mark and an object that exist. It fails if a lesson
  in the plan has no module or if a module defines a lesson that the plan does
  not mention. It also completes each `Exercise` block with what the site can
  show from `exercises/` (see [exercises.md](exercises.md)).

### `tools/`

| Program                                              | Function                                                                                                                            |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Downloads `docs/guides` of Qiskit/documentation to `.cache/qiskit-docs`, at the version in `qiskit-docs.commit`.                    |
| `extract.py`                                         | Converts those guides to plain text in `.cache/qiskit-docs/text`.                                                                   |
| `tts.py`                                             | Synthesizes the narration of a lesson and writes `timings.json`.                                                                    |
| `pronunciacion.py`                                   | Dictionary that rewrites English acronyms and names so the voice reads them well.                                                   |
| `verify.py`                                          | Runs the Python of the lessons, except `norun`, and compares the `Out(…, check=True)`.                                              |
| `practica.py`                                        | Runs each notebook with and without solutions. It also tests `mo.ui.slider`/`number` at minimum and maximum. A runtime error fails. |
| `exercises.py`                                       | Runs the solution and the starter code of each exercise with `qgcheck` and checks its `needs`.                                      |
| `serve.py`                                           | Serves `site/` on 127.0.0.1:8810 and adds `POST /run`, which grades an exercise with `qgcheck`.                                     |
| `playtest.py`, `seektest.py`, `shot.py`, `review.py` | Playwright tests and screenshots on the Qiskit course served on port 8810.                                                          |

`qiskit-docs.commit` holds the Qiskit/documentation hash that coverage is
checked against. To update the guides, change that hash, run
`tools/fetch_docs.py` and fix `plan.py` until `build.py` passes.

### `site/`

The root holds the catalog and what the courses share:

- `index.html` and `catalog.css` are the catalog, in English. It reads
  `courses.json`, which has one entry per course (`slug`, `title`, `summary`,
  `language`), and from each `<slug>/course.json` the number of lessons. It
  draws one card per course with a link to `<slug>/`. Adding a course is adding
  its folder and its entry.
- `theme.css` and `theme.js` are the theme of the catalog and of the courses:
  colors, fonts and the mode the reader picks. The labels of the theme control
  follow the page's `lang`. [design.md](design.md) describes them.
- `vendor/` is KaTeX and the two fonts, copied from `editor/node_modules` by
  `editor/vendor.js`. Git ignores it; `mise run install` and `mise run deploy`
  generate it again and first delete whatever was there. No page requests
  anything from another site except the Turnstile script, which `exercise.js`
  downloads from Cloudflare when the runner requires it.

`qiskit/` is the Qiskit course. Its pages link the theme and `vendor/` with
`../`, and call the platform routes by their absolute path:

- `index.html` is the course home page, styled by `index.css`. It reads
  `course.json` and requests in parallel the `lesson.json` of the completed
  lessons to build the review.
- `lesson.html` loads `engine.js`, the player, styled by `app.css`. `blocks.js`
  draws the course's own blocks, `exercise.js` the exercise block and `sfx.js`
  the sounds. KaTeX draws the formulas. Both pages load KaTeX with `defer`,
  before their own scripts.
- `account.js` is the account menu and `privacidad.html` the page that says what
  is stored.
- `editor.js` is the CodeMirror 6 editor of the exercises, bundled from
  `editor/`. It is described in
  [exercises.md](exercises.md#editor-in-the-lesson).
- `notebooks.js` writes the "how to run the notebooks" line that goes with each
  `marimo` command.
- `lessons/<id>/` holds `lesson.json`, `timings.json` and `audio/<step>.mp3`.
- `course.json` is the index: parts, lessons, minutes and missions.

### `practica/`

The marimo notebooks are the `.py` files in these folders that contain
`marimo.App(`. A notebook can import a module from its folder
(`proyecto/ising.py`), because `tools/practica.py` puts that folder on
`sys.path`. Each mission of a lesson names its notebook with `Mission(...)`.
`soluciones/<notebook>.json` (with `__` instead of `/` for notebooks in
subfolders) holds the (text, replacement) pairs that `tools/practica.py` applies
to check that all the verifications give ✅.

### `exercises/` and `qgcheck/`

`exercises/<lesson>/<exercise>/` holds `starter.py`, `solution.py` and
`check.py`. `qgcheck/spec.py` locates them, `qgcheck/runner.py` launches
`qgcheck/job.py` in a separate process (which in turn launches `qgcheck/host.py`
with the learner's code), and `qgcheck/__init__.py` gives `check.py` its
helpers. The format, the result of `grade()` and the checks are in
[exercises.md](exercises.md). `site/qiskit/exercise.js` draws the editor of each
exercise and calls `POST /run` on its own origin.

### `content/`

`<id>.cache.json` holds, for each clip of a lesson, the hash of what was said
and the time of each word. `tts.py` consults it so it does not synthesize again
a clip that did not change.

### `runner/`

The runner server ([runner.md](runner.md)) runs jobs in _slots_. There are
`QG_JOBS` slots, numbered from 0, and slot `n` always uses uid `20000 + n`. The
shared state is the `FREE_SLOTS` queue of free slots, in `server.py`.

| State | Meaning                                        | Who leaves it and when                                                                                                          |
| ----- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| free  | Its number is in `FREE_SLOTS`.                 | A request thread, in the `finally` of `do_POST`, once `run_job` has returned.                                                   |
| busy  | A request thread holds its number and uses it. | The same thread, after validating the request, with `get_nowait()`. If the queue is empty it answers 503 and waits for nothing. |

- Only the thread that took a slot returns it, and only after `run_job` killed
  the processes of that uid and deleted its directory and its files in
  `/scratch`, `/tmp`, `/var/tmp` and `/dev/shm`. That deletion is what isolates
  a job from the previous one, because the uid is reused.
- `run_job` starts a thread (`_Scan`) that measures memory and disk. Only that
  thread writes `peak` and `killed` (`killed` before `tripped`); `run_job` reads
  them after `tripped` or after joining the thread.
- The Cloudflare instances share nothing: each has its own queue. The Worker
  picks one of two and, if it answers 503, repeats the request once on the
  other, with its own budget reservation.
- The Worker keeps its state in two Durable Objects in
  `runner/worker/src/meters.ts` ([runner.md](runner.md#worker-protection)
  explains the limits). Each object serves one call at a time, and its methods
  only wait on their own storage, so reading and writing inside one method is
  one operation.

There is one `RateLimiter` per key (an IP or a user), label and day, named with
an HMAC of the three. Its state is the `count` record (clock minute, requests of
that minute and of the day).

| State    | Meaning                                     | Who leaves it and when                                                                                                                                                                |
| -------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| empty    | There is no `count`.                        | When the object is created, and the `alarm` alarm when the day plus one minute ends.                                                                                                  |
| counting | There is a `count` and an alarm at day end. | `take`, which the Worker calls on each `POST /run` and each request to `/auth` and `/api`. It adds a request if they fit in the minute and in the day, and otherwise changes nothing. |

- When the clock minute changes, `take` restarts the minute counter from zero
  without waiting for any event. The day counter continues until the alarm.
- Only `take` writes `count`, and only `alarm` deletes it.

There is one `Budget` in total. Its state is three kinds of record: `month` and
`day` (UTC period and nanodollars spent; `day` counts only public spend) and,
per instance, `awake:<instance>` (the instant it is expected to shut down and
the reservation that set it).

| State      | Meaning                                                                               | Who leaves it and when                                                                                                                                                                                            |
| ---------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| new period | There is no `month` (or `day`), or its period is not the current one: the total is 0. | The clock passing to day 1 UTC, or to a new day. There is no timer: the first `reserve` of the new period overwrites it.                                                                                          |
| reserved   | The total includes what is set aside for runs that have not finished.                 | `reserve`, which the Worker calls before starting the container. It adds the reservation only if the month cap fits (the public one or the total) and, for the public, the day cap; otherwise it changes nothing. |
| settled    | The total swaps the reservation for the measured cost, capped at what was set aside.  | `settle`, when the run ends and, at no cost, when Turnstile rejects a request that had already reserved. It does nothing if the period already changed.                                                           |

- `reserve` adds the awake window from `max(now, awakeUntil)` and leaves
  `awakeUntil` at `now` plus the reservation plus `sleepAfter`. `settle` only
  shortens it if the reservation that set it is still the owner; if another one
  extended it, that part stays charged.
- A request has one reservation per attempt, and each is set aside once and
  swapped once; or it is interrupted and the reservation stays in the total.
- A `settle` that fails is logged and does not change the response of the
  request.

`DB` is the D1 database of the accounts ([runner.md](runner.md#accounts) gives
the endpoints and [`schema.sql`](../runner/worker/src/schema.sql) the tables).
Everything hangs from `users` with `ON DELETE CASCADE`, and D1 enforces foreign
keys: deleting a user deletes everything of theirs in one statement. The
statements of a D1 batch run one after another, with no other write in between.

User (`users`):

| State    | Meaning                                                          | Who leaves it and when                                                                                                                       |
| -------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| absent   | There is no row with that id.                                    | The start; and `DELETE /api/me` or the daily cleanup, which delete the row.                                                                  |
| active   | There is a row and `seen_day` is the day of the last visit.      | `userForIdentity`, on the OAuth return of a new identity, in a batch with its `identities` row. Each visit with a session raises `seen_day`. |
| inactive | `seen_day` is earlier than today minus `ACCOUNT_RETENTION_DAYS`. | Time passing. There is no timer: the daily cleanup deletes it.                                                                               |

- Two first sign-ins at once of the same identity create a single user: the key
  of `identities` is (provider, identifier), the batch of the second is undone
  entirely and that sign-in uses the user of the first.
- A visit is a request with a session to `/run` or to `/api`, or the OAuth
  return. `seen_day` only rises, at most once a day.

Session (`sessions`):

| State   | Meaning                                       | Who leaves it and when                                                                |
| ------- | --------------------------------------------- | ------------------------------------------------------------------------------------- |
| valid   | There is a row and `expires_at` is after now. | `openSession`, on the OAuth return. Each sign-in creates one and leaves the previous. |
| expired | There is a row and `expires_at` has passed.   | Time passing. `sessionUser` no longer accepts it; the row stays until the cleanup.    |
| closed  | There is no row.                              | `POST /auth/logout`, the cleanup of the expired ones and the deletion of the user.    |

A session never becomes valid again. An account has as many at once as devices
it signed in on.

Progress (`lesson_done`, `exercise_state`, `kv` and `users.progress_version`):

| State     | Meaning                            | Who leaves it and when                                                   |
| --------- | ---------------------------------- | ------------------------------------------------------------------------ |
| empty     | The user has no rows in the three. | The creation of the user, with `progress_version` 0.                     |
| with data | It has rows in any of the three.   | `mergeProgress`, which serves `POST /api/merge` and `PUT /api/progress`. |

- A write removes nothing: it does not delete a lesson, `passed` does not go
  back to false, `hints`, `checks` and `at` only rise, and the code changes only
  with an edit with a greater `at`. Each `kv` key is merged by the rule of its
  family ([runner.md](runner.md#progress)). What does not change the result does
  not write.
- `mergeProgress` reads the three tables and `progress_version` in one batch,
  computes the result and writes it in another batch whose statements act only
  if `progress_version` is still the one read; the last one raises it by one. If
  another write of the same user slipped in, that last one changes no row and
  the request reads again. After 10 attempts it answers 503 `busy`. No write
  overwrites another.
- If the user is deleted while the request runs, the read does not find them and
  answers 401 `signed_out`.

Attempt (`attempts`):

| State    | Meaning                                                  | Who leaves it and when                                                                                            |
| -------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| recorded | There is a row, with `user_id` or with `NULL`.           | `recordAttempt`, after each 200 response of `/run` whose JSON has the shape of the contract.                      |
| expired  | `at` is earlier than now minus `ATTEMPT_RETENTION_DAYS`. | Time passing. The daily cleanup deletes it.                                                                       |
| deleted  | There is no row.                                         | The daily cleanup and, if it had a `user_id`, the deletion of the user. Anonymous ones leave only in the cleanup. |

A row is not modified after it is written.

Deletion and cleanup:

- `DELETE /api/me` deletes the `users` row. With it go the identities, the
  sessions, the progress and the attempts of the user. The following requests
  with their cookie no longer find the session.
- The daily cron runs `purge` in one batch, in this order: expired attempts,
  expired sessions, inactive users. An inactive user who signs in just while it
  runs can lose the session being opened (500); on retry a new account is
  created.

## Data path

```text
plan.py + parte*.py -> build.py -> lesson.json (and course.json)
lesson.json -> tts.py -> audio/<step>.mp3 + timings.json
lesson.json + timings.json + audio -> engine.js
```

1. `build.py` numbers the sections following the order of `plan.PARTS`, adds to
   each lesson the link to its original guides and writes `lesson.json` with the
   list of steps and `next`, the following lesson. `course.json` adds up the
   minutes: the duration from `timings.json` if it exists, or an estimate by
   words if not, plus 45 seconds per question.
2. `tts.py` reads `lesson.json`. For each step it applies `pronunciacion.py` to
   the `say` text, synthesizes `audio/<step>.mp3` with Edge TTS and measures its
   duration with `ffprobe`. `timings.json` holds per step `dur` (seconds),
   `marks` (the second at which the word after each `[[mark]]` starts) and
   `cues` (the subtitles with their start second, with the original text).
3. `engine.js` loads `lesson.json` and `timings.json`, plays the audio of each
   step and fires each action of `actions` at the second of its mark. The
   subtitles come from `cues`. `?beat=N` shows the final state of step N without
   audio.
