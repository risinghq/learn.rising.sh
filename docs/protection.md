# Worker protection

The container runs only for an account, because it is the one thing the site
pays for. The Worker checks every `POST /run` before it starts the container.
The checks run in this order, and the first that fails answers without the
container receiving anything:

1. The [session](#session): a request without an account session (`qg_auth`)
   answers 401.
2. The [per-IP limit](#per-ip-limit).
3. The per-user limit, unless the account belongs to a
   [maintainer](#maintainers).
4. The [size](#code-size) of the body and of the code.
5. The [budget](#budget) of the month and of the day.
6. [Turnstile](#turnstile), if the account is not a maintainer's and the request
   carries no valid Turnstile session.

Exercises of a course that grades in the browser (`runs: "browser"` in its
lesson, see [exercises.md](exercises.md#where-the-code-runs)) never call `/run`,
so none of these checks applies to them.

A refusal carries `{"error": "...", "reason": "..."}`. The editor shows the text
of `error` as it is. Every value comes from `env` in
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts); changing one is
editing that file and deploying. A missing value, or one that is not a positive
number, makes the Worker answer 500 `internal_error` and log which variable
failed.

`GET /health` is answered by the Worker with 200 without touching a container,
so that a request without a limit cannot keep an instance awake.

## Session

A `POST /run` with no valid account session answers 401 `signin_required` before
it counts against any limit and before Turnstile. The learner sees «Para
ejecutar código en el corredor hay que entrar con una cuenta.» The editor of an
exercise that runs in the container shows the exercise and the two sign-in links
in place of its run buttons while the browser holds no session, and it takes a
401 from `/run` on any host as the signal to do the same. `mise run serve`, the
local server that grades on the same machine with no accounts, is the one host
where the editor keeps its buttons until the first 401.

## Per-IP limit

| Variable          | Value | Meaning                               |
| ----------------- | ----- | ------------------------------------- |
| `RATE_PER_MINUTE` | 30    | Requests per IP in each clock minute. |
| `RATE_PER_DAY`    | 1000  | Requests per IP in each UTC day.      |

It counts every request to `/run` from the moment it arrives, also those that
are later rejected for size or Turnstile. Over the limit it answers 429 with
`Retry-After` in seconds and `reason` `rate_minute` or `rate_day`. The learner
sees:

- «Estás ejecutando demasiado seguido. Espera 12 s y vuelve a intentarlo.»
- «Llegaste al límite de ejecuciones de hoy. Puedes volver a ejecutar en 5 h.»

The IP is `CF-Connecting-IP`. Without that header (locally) all requests share
one counter. A whole class behind one IP shares the limit.

Every `/run` request has a session, so the per-IP cap is `SIGNED_IN_IP_FACTOR`
times those values (4: 120 per minute and 4000 per day), and what bounds each
learner is their own cap, with the same values of `RATE_PER_MINUTE` and
`RATE_PER_DAY`. So a whole class fits behind one IP, and a single learner spends
no more than the table says. `/auth` requests use the per-IP limit
`AUTH_PER_MINUTE` ([accounts.md](accounts.md#endpoints)) and `/api` requests
with a session use the per-user limit.

Each counter lives in a `RateLimiter` Durable Object named with an HMAC of the
label (`limiter` for an IP, `user`, `auth` or `api`), the day and the key (the
IP or the user id). The HMAC key comes from `TURNSTILE_SECRET`, so the name
cannot be turned back into an IP or a user without that secret. The object keeps
two counters, the minute's and the day's, and deletes its state when the day
ends.

## Code size

| Variable         | Value  | Meaning                          |
| ---------------- | ------ | -------------------------------- |
| `MAX_CODE_BYTES` | 20 000 | UTF-8 bytes of the `code` field. |

A body larger than six times the maximum plus 1024 bytes answers 413 without
being read whole. A body that is not JSON or has no `code` as text answers 400
`bad_request`. A larger code answers 413 `too_large` and the learner sees «El
código ocupa 20001 bytes y el máximo son 20000.». The container repeats the
check with `MAX_CODE` in `qgcheck/runner.py`; to change the cap, change both.

## Budget

Cloudflare has no spending cap: its budget alerts only send an email
([deploy.md](deploy.md#11-set-spend-alerts)). So the Worker counts what it
spends and refuses to run when the estimated spend of the month would reach
`MONTHLY_BUDGET_USD`. The count is an upper bound of what Cloudflare Containers
bills. It does not include the 5 USD a month of the Workers Paid plan, which is
paid apart.

| Variable                | Value      | Meaning                                                          |
| ----------------------- | ---------- | ---------------------------------------------------------------- |
| `MONTHLY_BUDGET_USD`    | 2          | Estimated spend of the UTC month that is not exceeded.           |
| `PUBLIC_BUDGET_SHARE`   | 0.75       | Share of the budget spent by whoever does not maintain the site. |
| `PUBLIC_BUDGET_DAYS`    | 15         | A day of public spend does not pass 1/15 of that share.          |
| `INSTANCE_TYPE`         | standard-1 | Instance type. The prices come from it.                          |
| `INSTANCES`             | 2          | Instances. The second serves a run only while the first is busy. |
| `RESERVED_BUSY_SECONDS` | 30         | Seconds a run sets aside from the budget before it starts.       |
| `MAINTAINERS`           | ids        | See [Maintainers](#maintainers).                                 |

`INSTANCE_TYPE` and `INSTANCES` are declared once in `cloudflare.config.ts`,
which uses them for the instance it deploys and for the Worker. There is no
price to edit: [`src/container.ts`](../runner/worker/src/container.ts) holds
Cloudflare's rate and the measures of each type.

### What a run costs

Cloudflare bills CPU only while the instance works, and memory and disk for the
whole time it is on, working or not. The instance shuts down 35 s
(`SLEEP_AFTER_SECONDS`) after its last request. Seconds are billed in steps of
10 ms. With `standard-1` (0.5 vCPU, 4 GiB and 8 GB) one second costs:

| Item              | Calculation                    | USD per second |
| ----------------- | ------------------------------ | -------------- |
| CPU, only working | 0.5 × 0.00002                  | 0.00001        |
| On, always        | 4 × 0.0000025 + 8 × 0.00000007 | 0.00001056     |

An isolated 2 s run, with no other in the previous 35 s, costs 2 × 0.00001 of
CPU plus 37 s on × 0.00001056: 0.00041 USD. Almost all of it is the wait. The
public's 0.10 USD a day covers about 240 of them. Runs that arrive while the
instance is on only extend its window, and the Worker sends every run to
instance 0 unless it is busy, so one learner's session keeps one instance on.
[runner.md](runner.md#sizing) gives the cost of a session and why this type and
window.

The Worker sets aside and charges like this, in the `Budget` Durable Object,
which keeps the spend of the month and of the day (this one counts only the
public) and, per instance, the instant it is expected to shut down
(`awakeUntil`):

1. Before it starts the container it sets aside the most expensive run that fits
   in `RESERVED_BUSY_SECONDS`: those seconds of CPU and the seconds on from
   `max(now, awakeUntil)` to `now + RESERVED_BUSY_SECONDS + 35 s`.
2. If the reservation does not fit, it does not run
   ([What is rejected](#what-is-rejected)). Checking and reserving is a single
   operation of the object, so several simultaneous requests cannot set aside
   together what fits only once.
3. When it ends it swaps the reservation for the measured cost: the time it
   waited for the container (start included) at the CPU rate and the on-window
   until 35 s after it answered, and never more than was set aside. If another
   run extended `awakeUntil` meanwhile, that part stays charged.
4. A request rejected after reserving (by Turnstile) gives back the whole
   reservation.

`RESERVED_BUSY_SECONDS` is a cap and not an estimate. It covers the 10 s of work
of [runner.md](runner.md#limits), the start of an instance and the retry after
a 503. If the run, with its retry, reaches that time, the Worker stops the
instance that had not answered, charges what was set aside and answers 504
`run_too_long`. The learner sees «La ejecución tardó más de lo que el corredor
permite y se detuvo. Revisa si el código tiene un bucle sin fin.» Since each run
costs at most what it set aside and is set aside only if it fits, the estimated
spend does not pass the budget. If the Worker is interrupted between reserving
and finishing, or storage fails at the end (logged with `where: "settle"`, the
response does not change), the reservation stays and the month counts too much,
never too little.

The sum of `cost_nano_usd` in the
[log](#what-the-container-receives-and-what-is-logged) gives the estimated spend
of the month. The estimate ignores the monthly allowances included in Workers
Paid and charges the CPU for the whole time the request waited for the
container. An instance the Worker fails to stop at the cap (logged with
`where: "stop"`) is billed until it shuts down by itself, and is left out of the
count.

### What is rejected

| Who        | Cap                                     | `reason`     |
| ---------- | --------------------------------------- | ------------ |
| Public     | 75 % of the budget, spent by everyone   | `budget`     |
| Public     | 1/15 of that 75 %, spent in the UTC day | `budget_day` |
| Maintainer | The whole budget, spent by everyone     | `budget`     |

A maintainer has no daily cap, and what they spend counts in the public's 75 %.
All refusals are 503 with `Retry-After` in seconds. `budget` waits for day 1 of
the next month and `budget_day` for UTC midnight. The learner sees:

- `budget`: «El corredor alcanzó su presupuesto de este mes y no ejecuta más
  código hasta que empiece el siguiente. Los cuadernos de marimo siguen
  funcionando en tu equipo.»
- `budget_day`: «El corredor alcanzó su presupuesto de hoy y no ejecuta más
  código hasta mañana. Puedes volver a ejecutar en 5 h. Los cuadernos de marimo
  siguen funcionando en tu equipo.»

With the 2 USD budget, whoever does not maintain the site has 1.5 USD a month
and 0.10 USD (1.5 over 15) a day.

### Maintainers

`MAINTAINERS` is a list of numeric GitHub ids separated by commas, not logins: a
login can be renamed and someone else can take it, and the id does not change.
With an empty list nobody is a maintainer. Whoever signed in with GitHub and has
their id in the list is a maintainer. They do not go through Turnstile, have no
per-user limit and spend from the whole budget. The per-IP limit and the code
size still apply to them. A Google account is never a maintainer, even if its
identifier is the same number. A value that is not a list of ids makes the
Worker answer 500 and log `MAINTAINERS`.
[deploy.md](deploy.md#10-choose-the-maintainers) says how to see the id of an
account.

## Turnstile

Cloudflare Turnstile is verified on the first run of each session, for a signed
in learner. Only a maintainer skips Turnstile: the request neither calls
`siteverify` nor receives `qg_session`. A request with no Turnstile session and
no token receives 403 `turnstile_missing` with the site key in the `sitekey`
field. With it, `site/player/exercise.ts` loads the widget and repeats the
request with the token in the `X-Turnstile-Token` header. The Worker checks it
with `siteverify`, to which it sends only the secret and the token, and if it is
valid it answers with the `qg_session` cookie besides the result:

```text
qg_session=<expiry>.<mac>; Max-Age=28800; Path=/run; HttpOnly; Secure; SameSite=Strict
```

The cookie carries the expiry time and a MAC that covers that time and the IP.
It carries no identifier, and it is no good from another IP or past its expiry.
The following runs send it by themselves and do not call Turnstile again.

| Response | `reason`                | The learner sees                                                                                       |
| -------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| 403      | `turnstile_missing`     | «Antes de ejecutar código hay que comprobar que eres una persona.»                                     |
| 403      | `turnstile_failed`      | «No pasó la comprobación de que eres una persona. Recarga la página e inténtalo de nuevo.»             |
| 503      | `turnstile_unavailable` | «No se pudo comprobar que eres una persona. Vuelve a intentarlo en unos segundos.» (`Retry-After: 10`) |

| Variable             | Value         | Meaning                                                 |
| -------------------- | ------------- | ------------------------------------------------------- |
| `SESSION_HOURS`      | 8             | Lifetime of the verified session.                       |
| `TURNSTILE_SITE_KEY` | configuration | The widget's public key, set in `cloudflare.config.ts`. |

`TURNSTILE_SECRET` is a Worker secret. The site key is not secret: the Worker
gives it to the page in the `turnstile_missing` response. With
`TURNSTILE_SITE_KEY` empty, a signed-in `POST /run` with no Turnstile session
answers 500 `internal_error` and logs the missing variable. Cloudflare documents
test keys that need no account, and the Worker tests use them:

| Key                                   | Type   | Behavior                                                          |
| ------------------------------------- | ------ | ----------------------------------------------------------------- |
| `1x00000000000000000000AA`            | site   | Always passes. The token it generates is `XXXX.DUMMY.TOKEN.XXXX`. |
| `1x0000000000000000000000000000000AA` | secret | Always passes.                                                    |
| `2x0000000000000000000000000000000AA` | secret | Always fails.                                                     |
| `3x0000000000000000000000000000000AA` | secret | Answers that the token was already used.                          |

## XP and friends

XP feeds the weekly board, so a script that posts XP would win it. The routes of
[accounts.md](accounts.md#xp) sit behind the same session and per-user limit as
the rest of `/api` (`RATE_PER_MINUTE` and `RATE_PER_DAY` per user), and these
caps bound what a user can earn and hold:

| Variable       | Value | Meaning                                              |
| -------------- | ----- | ---------------------------------------------------- |
| `XP_PER_DAY`   | 300   | XP a user earns in a UTC day, across all sources.    |
| `XP_PER_EVENT` | 50    | The largest `amount` one `POST /api/xp` may ask for. |
| `MAX_FRIENDS`  | 50    | Friends an account holds, checked on both sides.     |

- Past `XP_PER_DAY` the route answers 200 with `granted` 0 and
  `reason: "daily_cap"`, and the day's remaining XP is granted in part when an
  event does not fit.
- A `source` and `ref` earn XP once per UTC day. The cap and this rule count the
  UTC day, not the learner's, so changing the time zone does not open a second
  day of XP.
- `MAX_FRIENDS` bounds the rows the friends list and the board read for every
  request.
- A user holds 5 unused invite codes at a time. This number is not a variable.
- A user holds 5 push subscriptions. A subscription's address must be `https:`
  on a host of `PUSH_HOSTS`, so the cron cannot be made to post to a server the
  learner chose. This number is not a variable.

An `exercise` earns XP only after the server recorded a passing `/run` check for
that user. `amount` for the other sources is the client's claim, bounded by
these caps. The `browser` source is the XP of an exercise graded in the browser,
where the server never sees the run, so it is a claim like `drill`'s.

## CLI tokens

| Variable         | Value | Meaning                                       |
| ---------------- | ----- | --------------------------------------------- |
| `CLI_TOKEN_DAYS` | 90    | How long a token from `rising login` is good. |

The token of [`rising`](cli.md) is checked on every `/api` request, with the
per-user limit and without the `Origin` check, which only a browser can satisfy.
The CLI's XP is what it says it earned: `XP_PER_EVENT`, `XP_PER_DAY` and the
once-per-day rule above are the only bound, and there is no anti-cheat.

The device flow has no variable. `POST /auth/device/token` skips the per-IP
`AUTH_PER_MINUTE` count and answers 429 `slow_down` to a poll sooner than 5
seconds after the last one. A login code lives 10 minutes.

## What the container receives and what is logged

The container receives the body of the request and `Content-Type`. It does not
receive the cookie, the token or the IP.

The Worker writes these logs and no others. All have fixed fields, defined in
[`src/log.ts`](../runner/worker/src/log.ts).

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

   `outcome` is `ok`, `signin_required`, `rate_minute`, `rate_day`,
   `bad_request`, `too_large`, `budget`, `budget_day`, `turnstile_missing`,
   `turnstile_failed`, `turnstile_unavailable` or `run_too_long`. `mode` and
   `exercise` are copied only if they have the shape of a value of the contract.

2. An error line, instead of the one above, when the request fails because of an
   error in the Worker or in the configuration and answers 500 `internal_error`:

   ```json
   {
     "event": "run",
     "outcome": "internal_error",
     "status": 500,
     "error": "Error"
   }
   ```

   `error` is the name of the error class. `detail` carries the text only for a
   configuration error, which names a variable and no data.

3. A separate error line, besides the line of the request itself, when a later
   step fails and the request goes on. It carries `where` and no `status`:
   - `"settle"`: the budget settlement failed.
   - `"stop"`: stopping an instance at the reservation cap failed.
   - `"attempt"`: recording the attempt in the database failed.

4. An error line with `event` `auth`, `api` or `purge` when an endpoint of
   [accounts.md](accounts.md) or the daily cleanup fails. It carries `outcome`
   `internal_error`, `status` 500 and `error` with the class name. An endpoint
   answers 500 `internal_error`; the cleanup lets the cron fail.

No log carries the code, the IP, the token, the cookie or the text of an error.
`cloudflare.config.ts` turns on Workers Logs with the invocation log off, which
is the one that carries the request. What Cloudflare keeps from its network does
not depend on the Worker.
