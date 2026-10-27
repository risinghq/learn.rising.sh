# The code runner

The runner runs a learner's code with Qiskit and Qiskit Aer and returns what it
printed and the result of the cases of an exercise, in the format of
[`qgcheck.grade`](exercises.md#grade-code). It is a container image with an HTTP
server. It does not depend on the host: the same contract holds on Cloudflare
Containers and on Docker. It is the `POST /run` that the lesson editor calls,
with the isolation needed to expose it on a network; `tools/serve.py` answers it
on your machine without that isolation.

The messages the runner and the Worker return to the learner are in Spanish,
because the course is. This document quotes them as they are.

## Contract

`POST /run` with a JSON body:

| Field      | Type | Meaning                                                                            |
| ---------- | ---- | ---------------------------------------------------------------------------------- |
| `code`     | text | The learner's code, up to 20 000 bytes.                                            |
| `mode`     | text | `run` (default) runs the code. `check` also tests it with the exercise.            |
| `exercise` | text | `lesson/exercise`, for example `p1-quickstart/ghz`. Required with `mode: "check"`. |

It answers 200 with:

```json
{
  "passed": false,
  "stdout": "",
  "error": null,
  "tests": [
    {
      "name": "n = 2, 3 y 4",
      "visible": true,
      "passed": false,
      "message": "Con n = 2 salen ['00'], y deberían salir solo 00 y 11.",
      "hint": 1
    },
    {
      "name": "caso oculto 1",
      "visible": false,
      "passed": false,
      "message": "Con otros tamaños de n no salen solo 00…0 y 11…1.",
      "hint": null
    }
  ],
  "ms": 2438,
  "killed": null,
  "peak_mb": 169
}
```

- `passed` is true if `error` is `null` and, with `check`, there is at least one
  case and all pass.
- `stdout` joins standard output and standard error, in the order they were
  written. With `check` it is that of the learner's code when it loads, once,
  and what its functions print.
- `error` is the error of the learner's code, with its line, or the reason the
  runner stopped it. With an error, `tests` is empty.
- `tests` is empty with `mode: "run"`. A hidden case is called `caso oculto N`.
  `hint` is the number of the hint the case names, or `null`
  ([exercises.md](exercises.md)).
- `killed` is `time`, `memory`, `disk` or `output` when the runner killed the
  job for that limit, and `null` if not. It is `scan` if the read of memory or
  disk that watches the limits failed: unable to measure, the runner kills the
  job instead of letting it run without a cap, and writes the error in its
  output.
- `ms` is the time of the job inside the runner. `peak_mb` is the largest sum of
  the proportional memory (PSS) of the job's processes, measured every 0.5 s and
  when the resident memory passes the cap: a page shared among processes is
  split among them, so it counts once.

Other responses carry `{"error": "..."}`: 400 if the request is not valid, 404
if the exercise does not exist, 413 if the code exceeds 20 000 bytes or the body
121 024 (six times the code, which is what a control character takes in JSON,
plus the envelope) and 503 if no slot is free. `GET /health` answers 200.

## Limits

| Limit             | Value              | How it is applied                                                                  |
| ----------------- | ------------------ | ---------------------------------------------------------------------------------- |
| Time              | 10 s               | `sandbox.py` kills the process group and every process of the same uid.            |
| Memory            | 512 MB             | `sandbox.py` checks every 20 ms and kills if the proportional memory (PSS) passes. |
| Working directory | 64 MB              | `sandbox.py` measures the disk every 100 ms; a file does not exceed 16 MB.         |
| Processes/threads | 64                 | `RLIMIT_NPROC` on the uid of the slot.                                             |
| Output            | 64 KiB             | `sandbox.py` kills the job when it is exceeded.                                    |
| Network           | `AF_UNIX` only     | A seccomp filter in `launcher.py` denies `socket` of any other family.             |
| Writing           | its directory only | An unprivileged uid; `/scratch`, `/tmp` and `/app` belong to root.                 |

A job runs with the uid of its slot, with no capabilities and with
`no_new_privs`. When it ends, the processes of that uid are killed and its
directory and whatever it left in `/scratch`, `/tmp`, `/var/tmp` and `/dev/shm`
are deleted. The server runs as many jobs at once as it has slots (`QG_JOBS`,
default 1); the slot cycle is in [architecture.md](architecture.md#runner). The
other values change with `QG_WALL_S`, `QG_MEM_MB` and `QG_SCRATCH_MB`.

The job is `python -u -P -m qgcheck.job`, the same one that
[`qgcheck.grade`](exercises.md#grade-code) launches on your machine without the
limits above. With `mode: "run"` the learner's code runs in that process. With
`mode: "check"` there are two processes of the same uid:

- The checker (`qgcheck/job.py`) runs the cases of `check.py`. Before importing
  anything it installs Python's lazy-import filter
  (`sys.set_lazy_imports_filter`) for `qiskit_ibm_runtime` and
  `qiskit_mitigation`: their clients and `scipy` load when used, not when the
  package is imported. Then it declares itself non-dumpable and imports the
  libraries of `PRELOAD_ROOTS` (`qgcheck/source.py`) that the learner's code and
  `check.py` use.
- The learner's process (`qgcheck/host.py`) is a `fork` of the checker, made
  before reading `check.py`, so it inherits the already loaded libraries and no
  answer. It closes all descriptors except its end of a `socketpair` with the
  checker, runs the learner's code once and serves the requests one at a time in
  that same process: the top-level state passes from one to the next, as in the
  learner's interpreter, and its output shows once. It does not fork per request
  because the learner's code may already have created threads (Qiskit creates
  them when transpiling) and the child of a process with threads hangs.

Each access to `learner.<name>` in a case is a request over the socket: which
names exist, the value of one or its call. The messages are JSON with the length
in front (`qgcheck/wire.py`, up to 4 MiB) and carry an `id` that the checker
draws at random on each request. Only data travels: numbers, strings, lists,
tuples, dictionaries with string keys, `bytes`, NumPy arrays, `Statevector`,
`Operator`, `SparsePauliOp` and `QuantumCircuit` in QPY. Code is never
deserialized. A case that needs to pass or receive anything else (a class, a
`PassManager`, a `Target`, some axes) handles it in a function of `check.py`
marked `@inside`, which runs in the learner's process and returns data
([exercises.md](exercises.md#write-checkpy)).

The checker declares itself non-dumpable and the learner's process is born from
it before any expected value exists, so the learner reads or writes neither the
checker's memory nor opens its descriptors, and its only channel is the socket.
The learner decides the value each request returns, whether its function
computes it or not, and the cases judge that value outside its process. Since it
does not know the `id` until it receives the request, it cannot leave answers
written for the following ones: the checker discards any answer that does not
repeat the `id` and treats it as a broken channel. The learner can read
`check.py`: the runner protects the host and the grading, not the answer key.

## Files

| File                                 | Function                                                                                             |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `runner/server.py`                   | The HTTP server and the validation of the request.                                                   |
| `runner/sandbox.py`                  | Launches the job and watches time, memory, disk and output.                                          |
| `runner/launcher.py`                 | Sets the rlimits, drops the uid and installs the seccomp filter before the `exec`.                   |
| `qgcheck/job.py`                     | The job: the checker of `check` and the execution of `run`.                                          |
| `qgcheck/host.py`                    | The learner's process of `check`.                                                                    |
| `qgcheck/wire.py`                    | The message format between those two processes.                                                      |
| `qgcheck/`                           | The grader of [exercises.md](exercises.md). The image copies it unchanged.                           |
| `runner/Dockerfile`                  | The image. Python and uv come from `mise.toml`; the libraries, from the `runner` group of `uv.lock`. |
| `runner/local.py`                    | Builds the image and runs it with Docker and the isolation flags.                                    |
| `runner/bench.py`                    | Measures cold and warm latency.                                                                      |
| `runner/worker/`                     | The Cloudflare Worker: serves `site/` and starts the image as a Container.                           |
| `runner/worker/cloudflare.config.ts` | The Worker, the Container, the Durable Objects, the variables and the routes.                        |
| `runner/worker/wrangler.config.ts`   | The `site/` directory the Worker publishes as static files.                                          |
| `runner/worker/src/routes.ts`        | The routes that enter the Worker before the files.                                                   |
| `runner/worker/src/index.ts`         | The checks of [Worker protection](#worker-protection).                                               |
| `runner/worker/src/meters.ts`        | The Durable Objects `RateLimiter` and `Budget`.                                                      |
| `runner/worker/src/session.ts`       | The Turnstile session cookie and the call to `siteverify`.                                           |
| `runner/worker/src/throttle.ts`      | The per-key counter (IP or user) over `RateLimiter`.                                                 |
| `runner/worker/src/auth.ts`          | `/auth/*`: sign-in with Google and GitHub and sign-out.                                              |
| `runner/worker/src/account.ts`       | Users, identities and account sessions in D1.                                                        |
| `runner/worker/src/api.ts`           | `/api/*`: the account and its progress.                                                              |
| `runner/worker/src/progress.ts`      | The validation and the merge of the progress.                                                        |
| `runner/worker/src/attempts.ts`      | What is recorded of each run.                                                                        |
| `runner/worker/src/purge.ts`         | The daily cleanup.                                                                                   |
| `runner/worker/src/schema.sql`       | The schema of the D1 database.                                                                       |
| `tools/dashboard.py`                 | The operator dashboard: reads D1 and shows where learners get stuck.                                 |
| `runner/worker/src/http.ts`          | The responses and the origin check that `/auth` and `/api` share.                                    |
| `runner/worker/src/contract.ts`      | The shape of an exercise id.                                                                         |
| `runner/worker/src/log.ts`           | The only lines the Worker writes to its log.                                                         |
| `runner/worker/test/`                | The Worker tests with a fake container and a fake OAuth provider.                                    |
| `runner/worker/test/serve.ts`        | The same Worker locally, for the browser tests of the account.                                       |
| `site/qiskit/account.js`             | The account client: the menu, the merge on load and the send on write.                               |
| `site/qiskit/privacidad.html`        | The privacy page.                                                                                    |
| [`deploy.md`](deploy.md)             | The steps to publish your own copy.                                                                  |
| `exercises/<lesson>/<exercise>/`     | The image carries only the `check.py` of each.                                                       |

## Run it with Docker

```sh
python runner/local.py serve
```

It builds the `qg-runner` image if needed (`python runner/local.py build`),
starts it and prints its URL. It uses gVisor (`runsc`) if Docker has it
registered and `runc` if not; `--runtime` forces one. The container runs on an
internal Docker network, with no internet access, with a read-only file system
and no capabilities beyond `SETUID`, `SETGID`, `KILL`, `CHOWN`, `FOWNER`,
`DAC_OVERRIDE` and `SYS_PTRACE` (the runner uses the last to read the memory of
the learner's processes). It is reached by its IP, which works on Linux.

```sh
curl -s $URL/run -d '{"code": "print(2 + 2)"}'
```

## Tests and measurements

```sh
mise run test:integration
python runner/bench.py --runs 50
```

`tests/runner_test.py` builds the image, starts it and talks to `/run` over
HTTP. It covers the contract, that the result of each exercise is that of
`qgcheck.grade`, attempts to forge a result and each limit. It is skipped if
Docker does not respond.

```sh
mise run test:worker
```

The Worker tests (`runner/worker/test/`) start the real Worker in Cloudflare's
local runtime (Miniflare), with `site/` as static files and the same entry
routes as the deploy, and with a fake container that records each call, a local
D1 database and a fake OAuth provider that stands in for Google and GitHub. They
need no Docker or account. They check that `GET /` serves the catalog and
`GET /qiskit/` the course, and that the course pages do not answer at the root,
that `POST /run` returns the runner's JSON and each limit of
[Worker protection](#worker-protection) by its response and, with the fake
container, that a rejected request does not reach it. They also walk through
sign-in, the [account endpoints](#accounts), what is stored of each run and the
daily cleanup. Two tests call the real `siteverify` with the test keys and are
skipped if there is no network.

`tests/account_ui_test.py` starts `runner/worker/test/serve.ts`, which serves
that same Worker locally with the fake provider, and walks through it with a
browser: it finishes a lesson and fails a check without an account, signs in,
opens another browser with the same account, deletes the account and looks at
what remains on the server and in the browser. It runs inside
`mise run test:ui`.

## Cloudflare Containers

`runner/worker/` is a single Worker, `duo`, that serves the catalog, the
courses, the runner and the accounts on the same origin, `edu.rising.sh`: the
editor calls `/run` and the Turnstile session cookie is `SameSite=Strict`.

- The files of `site/` are its static files. The directory is set by
  [`wrangler.config.ts`](../runner/worker/wrangler.config.ts).
- `/run`, `/health`, `/auth/*` and `/api/*` enter the Worker code before the
  files (`run_worker_first`). The list is in
  [`src/routes.ts`](../runner/worker/src/routes.ts), which the deploy and the
  tests also use. A file of the site is answered by the file service without
  running the Worker: `/` is the catalog and `/qiskit/` the course. A route that
  is not a file goes to the Worker, which hands it back to the file service, and
  this answers 404. A route under `/auth/*` or `/api/*` that does not exist is
  answered by the Worker with 404 and `reason` `not_found`.
- A `Runner` class that extends `Container` (`@cloudflare/containers`) spreads
  the `/run` requests between two instances. If the chosen instance answers 503,
  it repeats the request once on the other. The instance has no internet access
  (`enableInternet = false`) and shuts down after 60 seconds without requests.

A single `cf deploy` builds the image, packages the Worker and uploads `site/`
as one version. To publish a change to the lessons, deploy again.

### What the operator sets

The Workers Paid plan, Docker, the D1 database, the Turnstile widget and the
OAuth clients belong to the account of whoever deploys. [deploy.md](deploy.md)
gives the steps. The values and the secrets the Worker reads are in
[Variables and secrets](#variables-and-secrets). The Worker is `duo`, serves on
`edu.rising.sh` (`domains: ["edu.rising.sh"]`) and does not use `workers.dev`.
Its Container is `duo-runner`.

## Accounts

An account is optional. Without it everything works and the progress stays in
the browser (`localStorage`). With it the progress is stored in a D1 database
and shared between devices. Sign-in is with Google or GitHub, without a
password.

| Method and route                   | What it does                                                                   |
| ---------------------------------- | ------------------------------------------------------------------------------ |
| `GET /auth/google`, `/auth/github` | Redirects to the provider. `?return=/path` says where to return (default `/`). |
| `GET /auth/<provider>/callback`    | The return from the provider. Opens the session and redirects to `return`.     |
| `POST /auth/logout`                | Closes the session. Answers 204.                                               |
| `GET /api/me`                      | Who signed in and their progress.                                              |
| `POST /api/merge`                  | Merges the browser's progress with the account's.                              |
| `PUT /api/progress`                | Saves progress changes. Answers 204.                                           |
| `DELETE /api/me`                   | Deletes the account and everything of theirs.                                  |

Error responses carry `{"error": "...", "reason": "..."}`. The methods that
change data (`POST`, `PUT`, `DELETE`) require the `Origin` header of the same
origin and answer 403 `bad_origin` if not. Without a session, all of `/api`
except `GET /api/me` answers 401 `signed_out`. A route that does not exist
answers 404 `not_found`, and a wrong method, 405 `method` with `Allow`.

### Sign-in

Sign-in is the OAuth 2.0 authorization code flow with `state` and PKCE (S256),
written without a library in [`src/auth.ts`](../runner/worker/src/auth.ts).

1. `GET /auth/<provider>` stores a random `state`, the PKCE verifier and the
   `return` in the `qg_oauth` cookie
   (`Path=/auth; HttpOnly; Secure; SameSite=Lax`, 10 minutes) and redirects to
   the provider. Google receives the `openid` scope; GitHub, none. `return` can
   only be a route of this site (it starts with a `/` and not with `//` or `/\`,
   has no control characters, up to 200 characters); anything else answers 400
   `bad_return`. The redirect percent-encodes (UTF-8) the characters that are
   not ASCII. Without the provider's credentials it answers 503
   `provider_unavailable`.
2. The return exchanges the code for a token at the provider's endpoint and
   reads from its data endpoint only the identifier: `sub` on Google, `id` on
   GitHub. Requests to GitHub carry `User-Agent: qiskit-guides`.
3. If the identifier already has a user, it signs in as that user; if not, one
   is created. A new session goes out in the `qg_auth` cookie
   (`Path=/; HttpOnly; Secure; SameSite=Lax`, `AUTH_SESSION_DAYS` days) and the
   response redirects to `return`. The `qg_oauth` cookie is spent on every
   return.

The return is rejected with 400 if the `qg_oauth` cookie is missing or belongs
to another provider (`flow_missing`), if the `state` is not the stored one
(`state_mismatch`), if it carries no `code` (`code_missing`) or if the provider
does not accept the code (`code_rejected`: a code is valid only once). If the
provider does not respond, 502 `provider_failed`. If the learner cancels on the
provider's screen, the response redirects to `return` without a session.

A provider and an identifier are an identity. Neither two providers nor two
accounts of the same provider merge: each new identity is a new user.

### Progress

`GET /api/me` answers `{"signedIn": false}` without a session. With one:

```json
{
  "signedIn": true,
  "providers": ["google"],
  "progress": {
    "done": ["p1-quickstart"],
    "exercises": {
      "p1-quickstart/ghz": {
        "code": "…",
        "hints": 1,
        "checks": 3,
        "passed": true,
        "at": 1760000000000
      }
    },
    "kv": { "qiskit:hitos": [1, 3] }
  }
}
```

`done` are the finished lessons. `exercises` holds per exercise the code (only
if the page sends it), the hints and the checks, whether it passed and `at`, the
Unix milliseconds of the last edit. `kv` holds the `localStorage` keys that
follow one of these shapes:

| Key                                     | Value              | When merging two values                                                  |
| --------------------------------------- | ------------------ | ------------------------------------------------------------------------ |
| `qiskit:heard:<lesson>`, `qiskit:hitos` | list of integers   | the union                                                                |
| `qiskit:misiones`                       | list of strings    | the union                                                                |
| `qiskit:pos:<lesson>`                   | integer            | the larger                                                               |
| `qiskit:predict:<lesson>:<id>`          | integer            | the one already there: a bet does not change                             |
| `qiskit:repaso`                         | `{id: {box, due}}` | per question, the higher box and, with equal boxes, the earlier due date |

`POST /api/merge` and `PUT /api/progress` receive the same body (`done`,
`exercises` and `kv`, all optional) and merge it with what is stored:

- `done` is united.
- Per exercise, `hints` and `checks` are the larger, `passed` is true if either
  was, and the code is that of the edit with the greater `at`. A missing or
  `null` code does not delete the stored one.
- `kv` is merged according to the table.

No rule depends on order, so two devices that sync end in the same state.
`POST /api/merge` answers `{"progress": {...}}` with the result;
`PUT /api/progress` answers 204. A `kv` key or a field the Worker does not know
answers 400 `bad_request`, so an error in the page shows. The body is
`application/json` (415 `content_type` if not) and up to 800 000 bytes (413
`too_large`). An account allows 500 lessons, 100 exercises and 2000 keys;
exceeding that answers 413 `too_much`. The code of an exercise is up to 20 000
bytes. Two simultaneous writes of the same user do not overwrite each other: one
that finds the progress changed reads and merges again. If it loses 10 times in
a row it answers 503 `busy` with `Retry-After`. The detail is in
[architecture.md](architecture.md#runner).

`DELETE /api/me` deletes the user and, through the foreign keys, their
identities, sessions, progress and attempts. It answers `{"deleted": true}` and
clears the cookie.

Each `/auth` endpoint counts against a per-IP limit, `AUTH_PER_MINUTE` per
minute and `RATE_PER_DAY` per day, and answers 429 `rate_auth` when exceeded.
Each `/api` endpoint counts against the per-user limit of
[Per-IP limit](#per-ip-limit).

### On the site

[`site/qiskit/account.js`](../site/qiskit/account.js) is the client. It puts the
_Entrar_ menu in the header of the course home page, the lessons and
[`privacidad.html`](../site/qiskit/privacidad.html), the page that says what is
stored, for how long and how to delete it.

- Without an account, the page makes no request except `/run`. What it looks at
  to know is the `qiskit:cuenta` mark in `localStorage`.
- _Entrar con Google_ and _Entrar con GitHub_ go to `/auth/<provider>` with
  `return` equal to the current page plus `#cuenta`. On return, that `#cuenta`
  makes the page leave the mark and merge the progress.
- With the mark, each load sends all the browser's progress to `POST /api/merge`
  and stores the response before the page reads it. It waits 4 seconds at most;
  if the Worker does not respond, the page continues with the local data. The
  first time you sign in, that same call merges what was already in the browser
  with the account's data.
- Each change is sent afterwards, in `PUT /api/progress`, 1.5 seconds after the
  last one and always when the page is closed or hidden. Without a network, the
  change stays in `localStorage` and the next load merges it.
- Each `qiskit:exercise:<id>` carries `at`, the time of the last edit of the
  code. It changes only when the code changes, not with hints or checks. This
  way the most recent copy wins when merging.
- The synced data are the finished lessons, the code, hints and checks of each
  exercise and the `kv` keys of the table above. The text of the reflections
  (`qiskit:reflect`) does not leave the browser. A value that the Worker would
  reject (a code of more than 20 000 bytes, for example) is left out of the
  body, because it would reject the whole body.
- _Cerrar sesión_ calls `POST /auth/logout` and _Borrar mi cuenta_, after a
  confirmation, `DELETE /api/me`. Neither touches what is in the browser. A 401
  response removes the mark.

The local progress passes to the account that signs in, whichever it is. On a
shared machine, whoever signs in afterwards merges what the previous user of the
browser left.

### Data stored

The Worker stores no email, name, avatar or password: it does not request them
from the provider and discards what the provider returns. The schema is
[`src/schema.sql`](../runner/worker/src/schema.sql).

| Table            | What it stores                                                           |
| ---------------- | ------------------------------------------------------------------------ |
| `users`          | A random id, the sign-up day and the day of the last visit.              |
| `identities`     | Provider and provider identifier of each user.                           |
| `sessions`       | The SHA-256 hash of the `qg_auth` token and its expiry. Never the token. |
| `lesson_done`    | The finished lessons and when.                                           |
| `exercise_state` | The code, hints, checks and whether it passed, per exercise.             |
| `kv`             | The `localStorage` keys of the table above.                              |
| `attempts`       | One row per run, with or without an account.                             |

Each 200 response of `/run` writes a row to `attempts`, from the JSON the
container returned, which is what grades the code. The row carries the moment,
the `user_id` (`NULL` without an account), the exercise, the mode, the result
(`pass`, `fail`, `error` or `timeout`), the names of the cases that failed, the
name of the Python exception (or `other`, or `killed_memory`, `killed_disk`,
`killed_output` or `killed_scan`), the hints the page says it used (`X-Hints`
header, a digit from 0 to 9), `ms` and the size of the code in bytes. It does
not carry the code, `stdout`, the error text or the `message` of a case, which
could repeat what the learner wrote. A run is recorded only with `mode` `run` or
`check` and an `exercise` shaped like a value of the contract. A failure to
write the row is logged and the response does not change.

### Retention

| Variable                 | Value | What is deleted                                             |
| ------------------------ | ----- | ----------------------------------------------------------- |
| `ATTEMPT_RETENTION_DAYS` | 180   | The attempts older than that many days.                     |
| `ACCOUNT_RETENTION_DAYS` | 730   | The accounts without a visit in that many days (24 months). |

A daily cron (`17 3 * * *`, UTC) calls the Worker's `scheduled` handler, which
deletes in a single batch the expired attempts, the expired sessions and the
inactive accounts. Deleting an account takes everything of theirs with it. A
visit is a request with an account session, and it is recorded at most once a
day.

### Where learners get stuck

`tools/dashboard.py` reads the database with `wrangler d1 execute` and writes
nothing. `uv run python tools/dashboard.py --database-id <uuid>` reads the
remote database, with the session of `bunx wrangler login` (in `runner/worker`)
or `CLOUDFLARE_API_TOKEN`, and `--local` reads the local copy of `--persist-to`.
For the period from `--since` to `--until` (UTC days, by default the last 30) it
prints the new users, those who tried something and the attempts with and
without an account; the lessons finished per lesson; the exercises with the most
failed checks and the cases that fail most; and the passed exercises with the
most hints opened. A failed check is a `check` attempt that did not end in
`pass`, and it counts without an account too. The finished lessons and the hints
come from the tables of an account, so they do not count anyone anonymous.
`--json` prints the same as JSON and `--limit` sets the rows of each ranking (10
by default).

### Variables and secrets

The secrets are created with `bindings.secret()` in
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts) and are not
written in the repository. [deploy.md](deploy.md) says where each is obtained
and how it is stored.

| Name                                       | Type   | What for                                                  |
| ------------------------------------------ | ------ | --------------------------------------------------------- |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | secret | The Google OAuth client.                                  |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | secret | The GitHub OAuth application.                             |
| `TURNSTILE_SECRET`                         | secret | The Turnstile widget; also the HMAC key of the counters.  |
| `DB`                                       | D1     | The database.                                             |
| `AUTH_PER_MINUTE`                          | 10     | Requests per IP and minute to `/auth/*`.                  |
| `AUTH_SESSION_DAYS`                        | 30     | Lifetime of the `qg_auth` cookie.                         |
| `SIGNED_IN_IP_FACTOR`                      | 4      | How much the per-IP cap of someone with an account rises. |
| `ATTEMPT_RETENTION_DAYS`                   | 180    | See [Retention](#retention).                              |
| `ACCOUNT_RETENTION_DAYS`                   | 730    | See [Retention](#retention).                              |

The Worker builds the `redirect_uri` from the origin of the request. What to
register with each provider is in [deploy.md](deploy.md).

## Worker protection

The Worker checks each `POST /run` before starting the container. The checks go
in this order, and the first that fails answers without the container receiving
anything:

1. The per-IP limit.
2. The per-user limit, if the request carries an account session (`qg_auth`)
   that does not belong to a maintainer.
3. The size of the body and of the code.
4. The budget of the month and of the day ([Budget](#budget)).
5. Turnstile, if the request is not from a maintainer and carries no valid
   Turnstile session.

A refusal carries `{"error": "...", "reason": "..."}`. The editor shows the
`error` text as is. All the values come from `env` in
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts); changing them
means editing that file and deploying. A missing value, or one that is not a
positive number, makes the Worker answer 500 with `internal_error` and log which
variable failed.

`GET /health` is answered by the Worker with 200 without touching a container,
so an unlimited request cannot keep an instance awake.

### Per-IP limit

| Variable          | Value | Meaning                               |
| ----------------- | ----- | ------------------------------------- |
| `RATE_PER_MINUTE` | 30    | Requests per IP in each clock minute. |
| `RATE_PER_DAY`    | 1000  | Requests per IP in each UTC day.      |

It counts every request to `/run` from the moment it arrives, including those
rejected later for size or by Turnstile. Past the limit it answers 429 with
`Retry-After` in seconds and `reason` `rate_minute` or `rate_day`. The learner
sees:

- "Estás ejecutando demasiado seguido. Espera 12 s y vuelve a intentarlo."
- "Llegaste al límite de ejecuciones de hoy. Puedes volver a ejecutar en 5 h."

The IP is `CF-Connecting-IP`. Without that header (locally) all requests share a
single counter. A whole class behind the same IP shares the limit.

With an account session, the per-IP cap is `SIGNED_IN_IP_FACTOR` times the
anonymous one (4: 120 per minute and 4000 per day) and what bounds each learner
is their own, with the same values of `RATE_PER_MINUTE` and `RATE_PER_DAY`. This
way a whole class with accounts fits behind one IP, and a single learner spends
no more than an anonymous one. The 429 response is the same, with `reason`
`rate_minute` or `rate_day`.

Each counter lives in a `RateLimiter` Durable Object named with an HMAC of the
label (`limiter` for an IP, `user`, `auth` or `api`), the day and the key (the
IP or the user id). The HMAC key comes from `TURNSTILE_SECRET`, so the name
cannot be traced back to an IP or a user without that secret. The object stores
two counters and deletes its state when the day ends.

### Code size

| Variable         | Value  | Meaning                          |
| ---------------- | ------ | -------------------------------- |
| `MAX_CODE_BYTES` | 20 000 | UTF-8 bytes of the `code` field. |

Code over the limit answers 413 with `reason` `too_large` and the learner sees
"El código ocupa 20001 bytes y el máximo son 20000.". A body larger than six
times the maximum plus 1024 bytes answers 413 without being read in full. A body
that is not JSON or has no `code` as a string answers 400 (`bad_request`). The
container repeats the check with `MAX_CODE` of `qgcheck/runner.py`; to change
the cap, change both.

### Budget

Cloudflare has no spend cap: its budget alerts only send an email
([deploy.md](deploy.md#10-set-spend-alerts)). So the Worker counts what it
spends and refuses to run when the estimated spend of the month would reach
`MONTHLY_BUDGET_USD`. The count is an upper bound of what Cloudflare Containers
bills. It does not include the 5 USD a month of the Workers Paid plan, which is
paid apart.

| Variable                | Value      | Meaning                                                          |
| ----------------------- | ---------- | ---------------------------------------------------------------- |
| `MONTHLY_BUDGET_USD`    | 2          | Estimated spend of the UTC month that is not exceeded.           |
| `PUBLIC_BUDGET_SHARE`   | 0.75       | Share of the budget spent by those who do not maintain the site. |
| `PUBLIC_BUDGET_DAYS`    | 15         | A day of public spend does not exceed 1/15 of that share.        |
| `INSTANCE_TYPE`         | standard-2 | Instance type. The prices come from it.                          |
| `INSTANCES`             | 2          | Instances the Worker spreads the runs between.                   |
| `RESERVED_BUSY_SECONDS` | 30         | Seconds a run sets aside from the budget before starting.        |
| `MAINTAINERS`           | ids        | See [Maintainers](#maintainers).                                 |

`INSTANCE_TYPE` and `INSTANCES` are declared once in
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts), which uses them
for the instance it deploys and for the Worker. There is no price to edit:
[`src/container.ts`](../runner/worker/src/container.ts) holds Cloudflare's rate
and the measures of each type, and from them come the price of the CPU second
and that of the awake-instance second.

#### What a run costs

Cloudflare bills CPU only while the instance works, and memory and disk for the
whole time it is awake, working or not. The instance shuts down `sleepAfter` (60
s) after its last request. With `standard-2` (1 vCPU, 6 GiB and 12 GB) one
second costs:

| Item              | Calculation                     | USD per second |
| ----------------- | ------------------------------- | -------------- |
| CPU, only working | 1 × 0.00002                     | 0.00002        |
| Awake, always     | 6 × 0.0000025 + 12 × 0.00000007 | 0.00001584     |

The Worker sets aside and charges like this, in the `Budget` Durable Object,
which stores per instance the instant at which it is expected to shut down
(`awakeUntil`):

1. Before starting the container it sets aside the most expensive run that fits
   in `RESERVED_BUSY_SECONDS`: those seconds of CPU and the awake seconds from
   `max(now, awakeUntil)` to `now + RESERVED_BUSY_SECONDS + sleepAfter`. An
   instance that was already awake charges only what the run extends its window.
   Seconds are charged in steps of 10 ms.
2. If the reservation does not fit, it does not run
   ([What is rejected](#what-is-rejected)). Checking and setting aside is a
   single operation of the object, so several simultaneous requests cannot set
   aside at once what fits only once.
3. When it ends it swaps the reservation for the measured cost: the time it
   waited for the container (the startup included) at the CPU rate and the awake
   window until `sleepAfter` after it answered, and never more than what was set
   aside. Only the reservation that set `awakeUntil` shortens it; if another
   extended it later, that part stays charged, because that other charged from
   where this one ended.
4. A request rejected after setting aside (by Turnstile) returns the whole
   reservation. The previous month and day totals are discarded.

`RESERVED_BUSY_SECONDS` is a cap and not an estimate. It covers the 10 s of work
of [Limits](#limits), the startup of an instance and the retry after a 503. If
the run, with its retry, reaches that time, the Worker stops the instance that
had not yet answered, charges what was set aside and answers 504 with `reason`
`run_too_long`. An instance that answered 503 serves another learner's job and
is not stopped. The retry sets aside its own reservation on the next instance.
The learner sees "La ejecución tardó más de lo que el corredor permite y se
detuvo. Revisa si el código tiene un bucle sin fin." Since each run costs at
most what it set aside and is only set aside if it fits, the estimated spend
does not exceed the budget. If the Worker is interrupted between setting aside
and finishing, or the storage fails on finishing (logged with `where: "settle"`
and the response does not change), the reservation stays and the month counts
too much, never too little.

#### An example with `standard-2`

Figures that come from the rates above, with `RESERVED_BUSY_SECONDS` of 30:

- **An isolated 2 s run**, with no other in the previous 60 s: 2 × 0.00002 of
  CPU plus 62 s awake (2 s of work and 60 of waiting) × 0.00001584. That is
  0.00102 USD. A 1 s run costs 0.00099 USD and a 10 s one, 0.00131 USD: almost
  all of it is the wait, not the work. Before starting it sets aside 0.0020256
  USD.
- **100 runs of 1 s in a minute**, spread between the two instances and
  back-to-back (50 s of work each): 100 × 0.00002 of CPU plus 2 instances awake
  110 s (50 of work and 60 of waiting) × 0.00001584. That is 0.0055 USD, less
  than 6 isolated runs cost, because the runs that arrive with the instance
  awake only extend its window. The same 100 runs, each more than 60 s after the
  previous one, cost 0.099 USD.
- **How many isolated 2 s runs fit in 2 USD**: 1955 in total. Those who do not
  maintain the site have 1.5 USD, which is 1466; the remaining 0.5 USD belongs
  to the maintainers. In a day the public spend does not exceed 0.10 USD (1.5
  USD divided by 15), which is 96 isolated runs.

#### What is rejected

| Who        | Cap                                     | `reason`     |
| ---------- | --------------------------------------- | ------------ |
| Public     | 75 % of the budget, spent by everyone   | `budget`     |
| Public     | 1/15 of that 75 %, spent in the UTC day | `budget_day` |
| Maintainer | The whole budget, spent by everyone     | `budget`     |

A maintainer has no daily cap, and what they spend counts toward the public's 75
%. All refusals are 503 with `Retry-After` in seconds. `budget` waits for day 1
of the next month and `budget_day` for UTC midnight. The learner sees:

- `budget`: "El corredor alcanzó su presupuesto de este mes y no ejecuta más
  código hasta que empiece el siguiente. Los cuadernos de marimo siguen
  funcionando en tu equipo."
- `budget_day`: "El corredor alcanzó su presupuesto de hoy y no ejecuta más
  código hasta mañana. Puedes volver a ejecutar en 5 h. Los cuadernos de marimo
  siguen funcionando en tu equipo."

#### Maintainers

`MAINTAINERS` is a list of numeric GitHub ids separated by commas, with no
logins: a login can be renamed and someone else can take it, and the id does not
change. Whoever signed in with GitHub and has their id in the list is a
maintainer. They do not go through Turnstile, do not have the per-user limit of
[Per-IP limit](#per-ip-limit) and spend from the whole budget. The per-IP limit
and the code size still apply to them. A Google account is never a maintainer,
even if its identifier is the same number. A value that is not a list of ids
makes the Worker answer 500 and log `MAINTAINERS`.
[deploy.md](deploy.md#9-choose-the-maintainers) says how to see the id of an
account.

#### What the estimate does not count

The count is an upper bound: it ignores the monthly quotas included in Workers
Paid, and it charges the CPU for all the time the request waited for the
container, the startup included, although Cloudflare bills it only while it
works. What may be left out:

- An instance that the Worker fails to stop on reaching the cap (logged with
  `where: "stop"`). Cloudflare bills it until it shuts down by itself.
- An instance that is still starting when the cap is reached has not answered
  yet, so the Worker stops it even if another learner reached it during startup.

The sum of `cost_nano_usd` in the log gives the estimated spend of the month.

### Turnstile

Cloudflare Turnstile is verified on the first run of each session, with or
without an account. Only a [maintainer](#maintainers) does not go through
Turnstile: the request neither calls `siteverify` nor receives `qg_session`. A
request without a Turnstile session and without a token receives 403
`turnstile_missing` with the site key in the `sitekey` field. With it,
`site/qiskit/exercise.js` loads the widget, and repeats the request with the
widget's token in the `X-Turnstile-Token` header. The Worker checks it with
`siteverify`, to which it sends only the secret and the token, and if valid it
answers with the `qg_session` cookie in addition to the result:

```text
qg_session=<expiry>.<mac>; Max-Age=28800; Path=/run; HttpOnly; Secure; SameSite=Strict
```

The cookie carries the expiry time and a MAC that covers that time and the IP.
It carries no identifier, and is not valid from another IP or past its expiry.
The following runs send it on their own and do not call Turnstile again.

| Response | `reason`                | The learner sees                                                                                       |
| -------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| 403      | `turnstile_missing`     | "Antes de ejecutar código hay que comprobar que eres una persona."                                     |
| 403      | `turnstile_failed`      | "No pasó la comprobación de que eres una persona. Recarga la página e inténtalo de nuevo."             |
| 503      | `turnstile_unavailable` | "No se pudo comprobar que eres una persona. Vuelve a intentarlo en unos segundos." (`Retry-After: 10`) |

| Variable             | Value         | Meaning                                                       |
| -------------------- | ------------- | ------------------------------------------------------------- |
| `SESSION_HOURS`      | 8             | Lifetime of the verified session.                             |
| `TURNSTILE_SITE_KEY` | configuration | The widget's public key configured in `cloudflare.config.ts`. |

`TURNSTILE_SECRET` is a Worker secret (`bindings.secret()`), not a repository
value. The site key is not secret: the Worker gives it to the page in the
`turnstile_missing` response. With `TURNSTILE_SITE_KEY` empty, an anonymous
`POST /run` answers 500 `internal_error` and logs the missing variable.
Cloudflare documents test keys that need no account:

| Key                                   | Type   | Behavior                                                          |
| ------------------------------------- | ------ | ----------------------------------------------------------------- |
| `1x00000000000000000000AA`            | site   | Always passes. The token it generates is `XXXX.DUMMY.TOKEN.XXXX`. |
| `1x0000000000000000000000000000000AA` | secret | Always passes.                                                    |
| `2x0000000000000000000000000000000AA` | secret | Always fails.                                                     |
| `3x0000000000000000000000000000000AA` | secret | Answers that the token was already used.                          |

The Worker tests use the three secrets.

### What the container receives and what is logged

The container receives the body of the request and `Content-Type`. It does not
receive the cookie, the token or the IP.

The Worker writes these logs and no others. All have fixed fields, which
`src/log.ts` defines.

1. A `run` line for each request to `/run` that the Worker answers, with any
   result except an internal error:

   ```json
   {
     "event": "run",
     "outcome": "ok",
     "status": 200,
     "mode": "check",
     "exercise": "p1-quickstart/ghz",
     "code_bytes": 212,
     "busy_ms": 930,
     "cost_nano_usd": 983732
   }
   ```

   `outcome` is `ok`, `rate_minute`, `rate_day`, `bad_request`, `too_large`,
   `budget`, `budget_day`, `turnstile_missing`, `turnstile_failed`,
   `turnstile_unavailable` or `run_too_long`. `mode` and `exercise` are copied
   only if they are shaped like a value of the contract.

2. An error line, instead of the previous one, when the request fails because of
   a Worker or configuration error and answers 500 `internal_error`:

   ```json
   {
     "event": "run",
     "outcome": "internal_error",
     "status": 500,
     "error": "Error"
   }
   ```

   `error` is the name of the error class. `detail` carries the text only if it
   is a configuration error, which names a variable and not data.

3. A separate error line, in addition to the line of the request itself, when a
   later step fails and the request carries on. It carries `where` and no
   `status`:
   - `"settle"`: the budget adjustment failed.
   - `"stop"`: stopping an instance on reaching the reservation cap failed.
   - `"attempt"`: recording the attempt in the database failed. The response
     does not change.

4. An error line with `event` `auth`, `api` or `purge` when an endpoint of
   [Accounts](#accounts) or the daily cleanup fails. It carries `outcome`
   `internal_error`, `status` 500 and `error` with the class name. An endpoint
   answers 500 `internal_error`; the cleanup lets the cron fail.

No log carries the code, the IP, the token, the cookie or the text of an error.
`cloudflare.config.ts` turns on Workers Logs with the invocation log off, which
is the one that carries the request. What Cloudflare stores from its network
does not depend on the Worker.

### Why these values

The values come from the Containers rates with the `standard-2` instance and two
instances that serve one job each (the figures of [Budget](#budget)):

- Two instances awake all month would cost about 82 USD (2 × 0.00001584 × 2 592
  000 s). With `sleepAfter` of 60 s and the 2 USD cap, the Worker cannot let
  that happen: each awake second is counted.
- 30 per minute is one run every 2 s. With 1 s runs an IP occupies 30 s of the
  120 s of instance there are each minute.
- 1000 per day, all of 1 s and isolated, would cost an IP 0.99 USD. The public
  daily cap (0.10 USD) stops it first.
- An attacker with many IPs spends at most 0.10 USD a day, which is 96 isolated
  2 s runs, so the public part of the month lasts at least 15 days. The
  maintainers keep the last 25 %.

These are calculations with those rates, not measurements of the deployed
Worker.
