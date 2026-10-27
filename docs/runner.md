# The code runner

The runner runs a learner's code with Qiskit and Qiskit Aer and returns what it
printed and the result of the cases of an exercise, in the format of
[`qgcheck.grade`](exercises.md#grade-code). It is a container image with an HTTP
server, and the same contract holds on Cloudflare Containers and on Docker. The
lesson editor calls it with `POST /run`. What the Worker checks before it calls
the runner is in [protection.md](protection.md). On your machine,
`tools/serve.py` answers `/run` without isolation.

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
  ([exercises.md](exercises.md#write-checkpy)).
- `killed` is `time`, `memory`, `disk` or `output` when the runner killed the
  job for that limit, and `null` if not. It is `scan` if the read of memory or
  disk that watches the limits failed: unable to measure, the runner kills the
  job instead of letting it run without a cap.
- `ms` is the time of the job inside the runner. `peak_mb` is the largest sum of
  the proportional memory (PSS) of the job's processes.

Other responses carry `{"error": "..."}`: 400 if the request is not valid, 404
if the exercise does not exist, 413 if the code exceeds 20 000 bytes or the body
121 024 (six times the code, which is what a control character takes in JSON,
plus 1024 for the envelope) and 503 if no slot is free. `GET /health`
answers 200.

## Limits

| Limit             | Value              | How it is applied                                                                                                                                          |
| ----------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Time              | 10 s               | `sandbox.py` kills the process group and every process of the same uid.                                                                                    |
| Memory            | 512 MB             | `sandbox.py` checks every 20 ms and kills if the proportional memory (PSS) passes. `RLIMIT_DATA` makes a large allocation fail earlier with `MemoryError`. |
| Working directory | 64 MB              | `sandbox.py` measures every 100 ms. More than 5000 entries count as a full disk.                                                                           |
| One file          | 16 MB              | `RLIMIT_FSIZE`.                                                                                                                                            |
| Processes/threads | 64                 | `RLIMIT_NPROC` on the uid of the slot.                                                                                                                     |
| Output            | 64 KiB             | `sandbox.py` kills the job when it is exceeded.                                                                                                            |
| CPU time          | time + 2 s         | `RLIMIT_CPU`.                                                                                                                                              |
| Network           | `AF_UNIX` only     | A seccomp filter in `launcher.py` denies `socket` of any other family.                                                                                     |
| Writing           | its directory only | An unprivileged uid. `/scratch`, `/tmp`, `/var/tmp` and `/app` belong to root.                                                                             |

The values change with `QG_WALL_S` (10), `QG_MEM_MB` (512) and `QG_SCRATCH_MB`
(64).

Memory is measured by reading the RSS every 20 ms, and the PSS when the RSS
passes the cap and, in any case, every 0.5 s. The PSS splits a page shared among
processes between them, so it counts once.

## Slots

The server runs as many jobs at once as it has slots (`QG_JOBS`, default 1).
Slot `n` always uses uid `20000 + n`. A job runs with that uid, with no
capabilities and with `no_new_privs`.

The numbers of the free slots are in the `FREE_SLOTS` queue of `server.py`. A
valid request takes a slot without waiting: if there is none, it answers 503.
Only the thread that took the slot returns it, and only after it kills the
processes of that uid and deletes its directory and whatever it left in
`/scratch`, `/tmp`, `/var/tmp` and `/dev/shm`. That cleanup isolates a job from
the previous one, because the uid is reused. Cloudflare instances share nothing:
each has its own slots.

## The job

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
  before `check.py` is imported, so it inherits the already loaded libraries and
  no expected value. It closes the inherited descriptors except input, output,
  error and its end of a `socketpair` with the checker, runs the learner's code
  once and serves the requests one at a time in that same process: the top-level
  state passes from one to the next and its output shows once. It does not fork
  per request because the learner's code may already have created threads
  (Qiskit creates them when transpiling) and the child of a process with threads
  hangs.

Each access to `learner.<name>` in a case is a request over the socket: which
names exist, the value of one or its call. The messages are JSON with the length
in front (`qgcheck/wire.py`, up to 4 MiB) and carry an `id` that the checker
draws at random on each request. Only data travels: numbers, strings, lists,
tuples, dictionaries with string keys, `bytes`, NumPy arrays, `Statevector`,
`Operator`, `SparsePauliOp` and `QuantumCircuit` in QPY. Code is never
deserialized. A case that needs to pass or receive anything else handles it in a
function of `check.py` marked `@inside`, which runs in the learner's process and
returns data ([exercises.md](exercises.md#write-checkpy)).

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

| File                 | Function                                                                                             |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| `runner/server.py`   | The HTTP server and the validation of the request.                                                   |
| `runner/sandbox.py`  | Launches the job and watches time, memory, disk and output.                                          |
| `runner/launcher.py` | Sets the rlimits, drops the uid and installs the seccomp filter before the `exec`.                   |
| `runner/Dockerfile`  | The image. Python and uv come from `mise.toml`; the libraries, from the `runner` group of `uv.lock`. |
| `runner/local.py`    | Builds the image and runs it with Docker and the isolation flags.                                    |
| `runner/bench.py`    | Measures cold and warm latency.                                                                      |
| `qgcheck/job.py`     | The job: the checker of `check` and the execution of `run`.                                          |
| `qgcheck/host.py`    | The learner's process of `check`.                                                                    |
| `qgcheck/wire.py`    | The message format between those two processes.                                                      |
| `qgcheck/`           | The grader of [exercises.md](exercises.md). The image copies it unchanged.                           |
| `exercises/*/*/`     | The image carries only the `check.py` of each exercise.                                              |
| `runner/worker/`     | The Worker that serves the site and starts the image. See below.                                     |

## On Cloudflare

`runner/worker/` is a single Worker, `duo`, that serves the catalog, the
courses, the runner and the accounts on the same origin, `edu.rising.sh`: the
editor calls `/run` and the Turnstile session cookie is `SameSite=Strict`. Its
Container is `duo-runner`.

- The files of `site/` are its static files. The directory is set by
  [`wrangler.config.ts`](../runner/worker/wrangler.config.ts).
- `/run`, `/health`, `/auth/*` and `/api/*` enter the Worker code before the
  files (`run_worker_first`). The list is in
  [`src/routes.ts`](../runner/worker/src/routes.ts), which the deploy and the
  tests also use. A file of the site is answered by the file service without
  running the Worker: `/` is the catalog and `/qiskit/` the course. A route that
  is not a file goes to the Worker, which hands it back to the file service, and
  this answers 404. A route under `/auth/*` or `/api/*` that does not exist is
  answered by the Worker with 404 and `reason` `not_found`. A `/run` that is not
  a `POST` answers 405 with `Allow: POST`.
- A `Runner` class that extends `Container` (`@cloudflare/containers`) spreads
  the `/run` requests between the two instances (`INSTANCES`). If the chosen
  instance answers 503, it repeats the request once on the other. The instance
  has no internet access (`enableInternet = false`) and shuts down after 60
  seconds without requests.

A single `cf deploy` builds the image, packages the Worker and uploads `site/`
as one version. To publish a change to the lessons, deploy again:
[deploy.md](deploy.md).

## Run it with Docker

```sh
python runner/local.py serve
```

It builds the `qg-runner` image if needed (`python runner/local.py build`),
starts it and prints its URL. It uses gVisor (`runsc`) if Docker has it
registered and `runc` if not; `--runtime` forces one. The container runs on an
internal Docker network, with no internet access, with a read-only file system,
`--memory 1g --cpus 1 --pids-limit 256 --ipc none`, and no capabilities beyond
`SETUID`, `SETGID`, `KILL`, `CHOWN`, `FOWNER`, `DAC_OVERRIDE` and `SYS_PTRACE`
(the runner uses the last to read the memory of the learner's processes). It is
reached by its IP, which works on Linux.

```sh
curl -s $URL/run -d '{"code": "print(2 + 2)"}'
```

## Tests

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
routes as the deploy, with a fake container that records each call, a local D1
database and a fake OAuth provider. They need no Docker or account. They cover
the routes, each limit of [protection.md](protection.md), the endpoints of
[accounts.md](accounts.md), what is stored of each run and the daily cleanup.
Two tests call the real `siteverify` of Turnstile with the test keys and are
skipped if there is no network.

`tests/account_ui_test.ts` starts `runner/worker/test/serve.ts`, which serves
that same Worker locally with the fake provider, and walks through it with a
browser. It runs inside `mise run test:ui`.
