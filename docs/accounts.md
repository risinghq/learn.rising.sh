# Accounts and progress

An account is optional. Without it everything works and the progress stays in
the browser (`localStorage`). With it the progress is stored in a D1 database
and shared between devices. Sign-in is with Google or GitHub, without a
password.

## Endpoints

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

Each `/auth` endpoint counts against a per-IP limit, `AUTH_PER_MINUTE` (10) per
minute and `RATE_PER_DAY` per day, and answers 429 `rate_auth` when exceeded.
Each `/api` request with a session counts against the per-user limit of
[protection.md](protection.md#per-ip-limit).

## Sign-in

Sign-in is the OAuth 2.0 authorization code flow with `state` and PKCE (S256),
written without a library in [`src/auth.ts`](../runner/worker/src/auth.ts).

1. `GET /auth/<provider>` stores a random `state`, the PKCE verifier and the
   `return` in the `qg_oauth` cookie
   (`Path=/auth; HttpOnly; Secure; SameSite=Lax`, 10 minutes) and redirects to
   the provider. Google receives the `openid` scope; GitHub, none. `return` can
   only be a route of this site (it starts with a `/` and not with `//` or `/\`,
   has no control characters, up to 200 characters); anything else answers 400
   `bad_return`. Without the provider's credentials it answers 503
   `provider_unavailable`.
2. The return exchanges the code for a token at the provider's endpoint and
   reads from its data endpoint only the identifier: `sub` on Google, `id` on
   GitHub. Each call to the provider waits 5 seconds at most.
3. If the identifier already has a user, it signs in as that user; if not, one
   is created. A new session goes out in the `qg_auth` cookie
   (`Path=/; HttpOnly; Secure; SameSite=Lax`, `AUTH_SESSION_DAYS` days, 30) and
   the response redirects to `return`. The `qg_oauth` cookie is spent on every
   return.

The return is rejected with 400 if the `qg_oauth` cookie is missing or belongs
to another provider (`flow_missing`), if the `state` is not the stored one
(`state_mismatch`), if it carries no `code` (`code_missing`) or if the provider
does not accept the code (`code_rejected`). If the provider does not respond,
502 `provider_failed`. If the learner cancels on the provider's screen, the
response redirects to `return` without a session.

A provider and an identifier are an identity. Neither two providers nor two
accounts of the same provider merge: each new identity is a new user. The
`redirect_uri` is built from the origin of the request; what to register with
each provider is in [deploy.md](deploy.md#4-create-the-google-client).

## Progress

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
Unix milliseconds of the last edit. `passed` is the server's record, never the
page's: it becomes true when `/run` with `mode: "check"` returns a passing
result for this user and exercise ([Data stored](#data-stored)). `kv` holds the
`localStorage` keys that follow one of these shapes:

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
- Per exercise, `hints` and `checks` are the larger, and the code is that of the
  edit with the greater `at`. A missing or `null` code does not delete the
  stored one. The `passed` the page sends must be present and a boolean, and is
  ignored: a guest's local passes do not reach the account.
- `kv` is merged according to the table.

A write removes nothing and no rule depends on order, so two devices that sync
end in the same state. `POST /api/merge` answers `{"progress": {...}}` with the
result; `PUT /api/progress` answers 204.

| Limit                   | Value                                 | Response           |
| ----------------------- | ------------------------------------- | ------------------ |
| Body type               | `application/json`                    | 415 `content_type` |
| Body size               | 800 000 bytes                         | 413 `too_large`    |
| Lessons in the body     | 500                                   | 400 `bad_request`  |
| Exercises in the body   | 100                                   | 400 `bad_request`  |
| `kv` keys in the body   | 2000                                  | 400 `bad_request`  |
| Value of a `kv` key     | 64 000 bytes                          | 400 `bad_request`  |
| Elements of a list      | 1000                                  | 400 `bad_request`  |
| Code of an exercise     | 20 000 bytes                          | 400 `bad_request`  |
| Unknown key or field    |                                       | 400 `bad_request`  |
| The account after merge | 500 lessons, 100 exercises, 2000 keys | 413 `too_much`     |

An unknown field answers 400 so that an error in the page shows.

Two simultaneous writes of the same user do not overwrite each other.
`mergeProgress` reads the progress and `users.progress_version` in one batch,
computes the result and writes it in another batch whose statements act only if
`progress_version` is still the one read. If another write got in, it reads and
merges again. After 10 attempts it answers 503 `busy` with `Retry-After`.

`DELETE /api/me` deletes the user and, through the foreign keys, their
identities, sessions, progress and attempts. It answers `{"deleted": true}` and
clears the cookie.

## On the site

[`site/account.ts`](../site/account.ts) is the client. It puts the _Entrar_ menu
in the header of the course home pages, the lessons and
[`privacidad.html`](../site/privacidad.html), the page that says what is stored,
for how long and how to delete it.

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
  code. It changes only when the code changes, so the most recent copy wins when
  merging.
- The synced data are the finished lessons, the code, hints and checks of each
  exercise and the `kv` keys of the table. The text of the reflections
  (`qiskit:reflect`) does not leave the browser. A value that the Worker would
  reject (a code of more than 20 000 bytes, for example) is left out of the
  body, because it would reject the whole body.
- _Cerrar sesión_ calls `POST /auth/logout` and _Borrar mi cuenta_, after a
  confirmation, `DELETE /api/me`. Neither touches what is in the browser. A 401
  response removes the mark.

The local progress passes to the account that signs in, whichever it is. On a
shared machine, whoever signs in afterwards merges what the previous user of the
browser left.

## Data stored

The Worker stores no email, name, avatar or password: it does not request them
from the provider and discards what the provider returns. The schema is
[`src/schema.sql`](../runner/worker/src/schema.sql). There are no migrations: a
schema change is to delete the database and create it again
([deploy.md](deploy.md#2-create-the-database)). Everything hangs from `users`
with `ON DELETE CASCADE`.

| Table            | What it stores                                                                    |
| ---------------- | --------------------------------------------------------------------------------- |
| `users`          | A random id, the sign-up day, the day of the last visit and the progress version. |
| `identities`     | Provider and provider identifier of each user.                                    |
| `sessions`       | The SHA-256 hash of the `qg_auth` token and its expiry. Never the token.          |
| `lesson_done`    | The finished lessons and when.                                                    |
| `exercise_state` | The code, hints, checks and whether it passed, per exercise.                      |
| `kv`             | The `localStorage` keys of the table above.                                       |
| `attempts`       | One row per run, with or without an account.                                      |

A visit is a request with a session to `/run` or `/api`, or the OAuth return. It
raises `seen_day` at most once a day.

Each 200 response of `/run` writes a row to `attempts`, from the JSON the
container returned, which is what grades the code. The row carries the moment,
the `user_id` (`NULL` without an account), the exercise, the mode, the result
(`pass`, `fail`, `error` or `timeout`), the names of the cases that failed, the
name of the Python exception (or `other`, or `killed_memory`, `killed_disk`,
`killed_output` or `killed_scan`), `ms` and the size of the code in bytes. It
does not carry the code, `stdout`, the error text or the `message` of a case,
which could repeat what the learner wrote. A run is recorded only with `mode`
`run` or `check` and an `exercise` shaped like an exercise id. A failure to
write the row is logged and the response does not change. A row is not modified
after it is written.

The same step sets `exercise_state.passed` to 1, creating the row if needed,
when the attempt has an account, `mode` `check` and the result `pass`. It is the
only writer of that column and nothing clears it, so the retention of attempts
does not undo a pass. A pass is never granted to a guest, to a `run`, or by a
progress write.

## Retention

| Variable                 | Value | What is deleted                                             |
| ------------------------ | ----- | ----------------------------------------------------------- |
| `ATTEMPT_RETENTION_DAYS` | 180   | The attempts older than that many days.                     |
| `ACCOUNT_RETENTION_DAYS` | 730   | The accounts without a visit in that many days (24 months). |

A daily cron (`17 3 * * *`, UTC) calls the Worker's `scheduled` handler, which
deletes in a single batch the expired attempts, the expired sessions and the
inactive accounts, in that order. Deleting an account takes everything of theirs
with it.

## Where learners get stuck

`tools/dashboard.ts` reads the database with `wrangler d1 execute` and writes
nothing.

```sh
bun tools/dashboard.ts --database-id <uuid>
```

It reads the remote database, with the session of `bunx wrangler login` (in
`runner/worker`) or `CLOUDFLARE_API_TOKEN`. `--local` reads the local copy of
`--persist-to`; `--database` names the database (the one of
[deploy.md](deploy.md#2-create-the-database)) and `QG_D1_ID` can give the uuid.
For the period from `--since` to `--until` (UTC days, by default the last 30) it
prints the new users, those who tried something and the attempts with and
without an account; the lessons finished per lesson; the exercises with the most
failed checks and the cases that fail most; and the passed exercises with the
most hints opened. A failed check is a `check` attempt that did not end in
`pass`, and it counts without an account too. The finished lessons and the hints
come from the tables of an account, so they do not count anyone anonymous.
`--json` prints the same as JSON and `--limit` sets the rows of each ranking (10
by default).
