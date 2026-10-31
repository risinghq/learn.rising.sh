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
| `POST /auth/logout`                | Closes the session. Answers 204. With a `Bearer` token, revokes that token.    |
| `GET /auth/device`                 | The page where a learner approves a CLI code. `?code=` fills it in.            |
| `POST /auth/device/code`           | Starts the [CLI login](#command-line): returns a device code and a user code.  |
| `POST /auth/device/token`          | The CLI polls it with the device code until the learner decides.               |
| `POST /auth/device/approve`        | The page's form: approves or denies a user code. Needs a session.              |
| `GET /api/me`                      | Who signed in and their progress.                                              |
| `POST /api/merge`                  | Merges the browser's progress with the account's.                              |
| `PUT /api/progress`                | Saves progress changes. Answers 204.                                           |
| `DELETE /api/me`                   | Deletes the account and everything of theirs.                                  |
| `POST /api/xp`                     | Records XP for a drill, exercise, lesson or CLI task.                          |
| `GET /api/xp`                      | The XP of the UTC day and of the local day: `{total, cap, today}`.             |
| `GET /api/streak`                  | The streak: `{current, longest, today}`.                                       |
| `POST /api/friends/invite`         | Returns a single-use code to share.                                            |
| `POST /api/friends/accept`         | Spends a code and makes a mutual friendship.                                   |
| `GET /api/friends`                 | Lists friends with their streak and XP this week.                              |
| `DELETE /api/friends/:id`          | Removes a friend for both sides. Answers 204.                                  |
| `GET /api/board`                   | The weekly board of the user and their friends.                                |
| `GET /api/push`                    | The VAPID public key and the reminder hour. 503 without the VAPID secrets.     |
| `POST /api/push`                   | Stores a browser's push subscription for the reminder. Answers 204.            |
| `DELETE /api/push`                 | Removes a subscription by its `endpoint`. Answers 204.                         |

Error responses carry `{"error": "...", "reason": "..."}`. The methods that
change data (`POST`, `PUT`, `DELETE`) require the `Origin` header of the same
origin and answer 403 `bad_origin` if not. Without a session, all of `/api`
except `GET /api/me` answers 401 `signed_out`. A route that does not exist
answers 404 `not_found`, and a wrong method, 405 `method` with `Allow`.

A request that carries `Authorization: Bearer <token>` is not a browser's: it is
exempt from the `Origin` check, and the token alone signs it in. Only a token
that [`rising login`](#command-line) issued works there; a missing, expired or
revoked one answers 401 `token_invalid`, and the cookie is not tried instead.

Each `/auth` endpoint counts against a per-IP limit, `AUTH_PER_MINUTE` (10) per
minute and `RATE_PER_DAY` per day, and answers 429 `rate_auth` when exceeded,
except `POST /auth/device/token`, which its own interval bounds. Each `/api`
request with a session or a token counts against the per-user limit of
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

## Command line

[`rising`](cli.md) signs in with the device flow of RFC 8628, in
[`src/device.ts`](../runner/worker/src/device.ts). The Worker serves the
approval page itself, in Spanish, because it needs the session cookie.

1. `POST /auth/device/code` returns `deviceCode` (a random 256-bit secret),
   `userCode` (eight characters shown as `ABCD-EFGH`), `verificationUri`,
   `verificationUriComplete`, `expiresIn` (600 seconds) and `interval` (5).
2. The learner opens `verificationUriComplete`, signs in with Google or GitHub
   if the browser has no session, and presses «Aprobar» or «Rechazar». The form
   posts to `POST /auth/device/approve`, which needs the session cookie and the
   `Origin` check. It answers 404 for an unknown code, 410 for an expired one,
   409 for one already decided and 401 without a session.
3. The CLI posts `{"deviceCode": "..."}` to `POST /auth/device/token` every
   `interval` seconds. Until the learner decides it answers 400
   `authorization_pending`. A poll sooner than `interval` answers 429
   `slow_down` with `Retry-After`. A denial answers 403 `access_denied`. An
   unknown or spent code answers 400 `invalid_code`, and an expired one 400
   `expired_code`. An approval answers 200 with `{token, expiresAt}` once: the
   code is spent and a second poll gets `invalid_code`.

The token is `rs_` and 43 random characters. It is a row of `sessions` with
`kind` `cli`, so it is stored only as a SHA-256 hash, expires after
`CLI_TOKEN_DAYS` ([protection.md](protection.md#cli-tokens)) and is deleted with
the account. A `web` session cookie is not accepted as a token, nor the other
way round. `POST /auth/logout` with the `Bearer` header deletes the row and
answers 204, also when the token was already gone.

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
`localStorage` keys that follow one of these shapes. `<course>` is the slug of
the course, 1 to 40 characters from `a-z`, `0-9` and `-`:

| Key                                         | Value                         | When merging two values                                                          |
| ------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------- |
| `<course>:heard:<lesson>`, `<course>:hitos` | list of integers              | the union                                                                        |
| `<course>:misiones`                         | list of strings               | the union                                                                        |
| `<course>:pos:<lesson>`                     | integer                       | the larger                                                                       |
| `<course>:predict:<lesson>:<id>`            | integer                       | the one already there: a bet does not change                                     |
| `<course>:repaso`                           | list of `{item, at, correct}` | the union by `item` and `at`, a miss beating a right answer; the latest 800 stay |

A `<course>:repaso` value in another shape, such as the boxes of the earlier
review, does not sync: `account.ts` removes it on load.

The keys under `rising:` (the mode, the speed, the XP) stay in the browser.

`POST /api/merge` and `PUT /api/progress` receive the same body (`done`,
`exercises` and `kv`, all optional) and merge it with what is stored:

- `done` is united.
- Per exercise, `hints` and `checks` are the larger, and the code is that of the
  edit with the greater `at`. A missing or `null` code does not delete the
  stored one. The `passed` the page sends must be present and a boolean, and is
  ignored: a guest's local passes do not reach the account.
- `kv` is merged according to the table.

A write removes nothing and no rule depends on order, so two devices that sync
end in the same state. `POST /api/merge` answers
`{"progress": {...}, "account": "…"}` with the result and the id of the account;
`PUT /api/progress` answers 204.

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

## XP

`POST /api/xp` records XP. The body is JSON with these fields and no others:

| Field      | Value                                                                                            |
| ---------- | ------------------------------------------------------------------------------------------------ |
| `source`   | `drill`, `exercise`, `lesson` or `cli`.                                                          |
| `ref`      | The item id. An exercise is `lesson/exercise`; a lesson is its slug.                             |
| `amount`   | An integer from 1 to `XP_PER_EVENT`.                                                             |
| `tz`       | Optional. The learner's IANA time zone, such as `America/Lima`. Stored on the user.              |
| `earnedAt` | Optional. When the learner earned the XP, in Unix milliseconds. A resend carries the same value. |

```json
{
  "source": "drill",
  "ref": "qiskit:1761800000000",
  "amount": 11,
  "tz": "America/Lima"
}
```

```json
{ "granted": 5, "total": 35, "cap": 300, "reason": null }
```

`granted` is the XP stored, `total` the XP of the UTC day so far and `reason`
says why `granted` is less than `amount`:

- `ref_today`: that `source` and `ref` already earned XP in this UTC day. It
  grants 0 whatever `amount` is.

The day is the one of `earnedAt` when it falls in the last 48 hours, and the one
of the request otherwise. The same day sets the cap, the streak and the week on
the board, so a resend after midnight is still the same award.

- `daily_cap`: the day has reached `XP_PER_DAY`. When only part of `amount`
  fits, the part is granted and `reason` is `null`.

Both answer 200, so a client can resend an event safely. A request with no
granted XP stores no row. An `exercise` with no passing check recorded by the
server for this user answers 403 `not_passed`. It is the same record as `passed`
in [Progress](#progress): the page and `PUT /api/progress` cannot set it. A body
that does not follow the table answers 400 `bad_request`.

For `drill` and `cli` the `ref` is any id of letters, digits and `_ . : -`, up
to 100 characters, so the CLI sends `lesson:exercise`. `GET /api/xp` answers
`{"total": 35, "cap": 300, "today": 20}`: the XP of the UTC day so far,
`XP_PER_DAY`, and the XP of the learner's local day, which is the day the streak
counts.

`amount` is what the client says it earned. The Worker bounds it with
`XP_PER_EVENT`, `XP_PER_DAY` and the once-per-day rule, and verifies only
`exercise`. The values are in [protection.md](protection.md#xp-and-friends).

The site posts three kinds:

- A drill session sends one `drill` post when it ends, with
  `<course>:<start of the session>` as `ref`.
- Finishing a lesson sends a `lesson` post with the lesson slug.
- The first passing check of an exercise sends an `exercise` post with
  `lesson/exercise`. An exercise graded in the browser sends it with the source
  `browser`, because the server never saw that run.

Each owner has one queue in `localStorage`: `rising:xpq:<account id>` for an
account, and `rising:xpq:anon` for XP earned before any sign-in. A post is
`source`, `ref`, `amount` and `earnedAt`. The id of the account is what
`POST /api/merge` answers in `account`, and `rising:cuenta` holds it.

A signed-in browser queues each post in its account's queue and sends it at
once, or when the browser comes back online. It reads only that queue, so it
never sends the posts of another account. The queue keeps a post until the
Worker answers. A 401, a 429 or a server error keeps it for the next try, and
any other refusal drops it. The queue stamps each post with `earnedAt` once, and
the once-per-day rule makes a resend safe.

Two events move a post between queues, and only these:

- **Sign-in:** the anonymous queue is appended to the queue of the account that
  signs in, and the anonymous key is deleted.
- **First load after an update:** the single `rising:xpq` of an earlier version
  moves to the anonymous queue, with `earnedAt` 0 and the source `drill`, if no
  account was ever signed in on the browser. Otherwise it is deleted.

Signing out leaves every queue where it is. The account's posts are sent the
next time that account signs in.

The header shows the streak and today's XP from the account: the browser keeps
the last `GET /api/streak` and `GET /api/xp` answers in `rising:tally` and adds
the posts still in the account's queue whose `earnedAt` is today in the
browser's time zone. A post with `earnedAt` 0 never counts. Without an account
the header counts the XP of this browser.

The first time a browser signs in, the XP it earned that day before signing in
is posted once, as `drill` posts with the ref `local:<day>:<k>` in chunks of up
to `XP_PER_EVENT`. They go through the anonymous queue. `rising:xpsent` marks it
done, and it also tells the update that an account signed in on the browser. The
Worker stamps a post with the moment it arrives, so the XP counts for the day of
signing in.

## Streaks

A day counts when the user earns at least 1 XP on it. The day is the local day
in the user's time zone when the XP was recorded; the zone is the last `tz` sent
(UTC until one is). The streak keeps the days already counted, so changing the
zone does not move past days. A day before the last counted one adds nothing.

`GET /api/streak` answers:

```json
{ "current": 8, "longest": 12, "today": true }
```

`current` is the run of days ending today, or yesterday if today has no XP yet.
`today` says whether today has XP. `longest` is the best run ever.

Freezes cover missed days. One is earned for every 7 days of a streak and at
most 2 are held. Each missed day between two days with XP spends one. When there
are fewer freezes than missed days the streak ends and the freezes are gone. A
gap that is still open, such as yesterday, counts as covered in `current` if a
freeze is held, and the freeze is spent only when XP arrives. The `streaks` row
of each user holds the run, the longest run, the freezes held and the last day.
Each stored XP event folds its day into that row in the same batch, so a read
never scans XP history.

## Streak reminder

A learner opts in from the end of a session or from the friends page. The
browser asks for notification permission, subscribes with the public key of
`GET /api/push` and sends the subscription to `POST /api/push`:

```json
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": { "p256dh": "...", "auth": "..." }
}
```

`DELETE /api/push` takes `{"endpoint": "..."}` and removes it. Each user keeps
at most 5 browsers (429 `too_many_browsers`). The `endpoint` must be `https:`
and on a host of `PUSH_HOSTS` (400 `bad_endpoint`), so a learner cannot make the
Worker post to a server of their choosing. Without the three VAPID secrets
[deploy.md](deploy.md#6-create-the-push-keys) creates, `GET /api/push` and
`POST /api/push` answer 503 `push_unavailable` and the site shows no opt-in.

An hourly cron (`17 * * * *`, UTC) sends one reminder at 19:00 in each learner's
own time zone (`users.time_zone`) to a learner who has all of these:

- a streak that is still alive;
- no XP yet on their local day;
- a subscribed browser;
- no reminder yet on this local day (`users.reminded_day`, set in the same
  statement that claims the send, so a repeated run sends nothing twice).

The push is encrypted as RFC 8291 `aes128gcm` and signed with VAPID. It goes to
every browser of the learner. A push service that answers 404 or 410 has dropped
the subscription, and the Worker deletes it. The service worker shows the
notification and opens `/` when the learner taps it.

## Friends

`POST /api/friends/invite` answers a code like `K7M2P-9XQ4T` and when it
expires, in Unix milliseconds:

```json
{ "code": "K7M2P-9XQ4T", "expiresAt": 1761500000000 }
```

The code is single-use and expires 7 days after it is issued. A user may hold 5
unused codes; the sixth answers 429 `too_many_invites`. The database stores the
hash of the code.

`POST /api/friends/accept` with `{"code": "K7M2P-9XQ4T"}` spends the code and
makes the friendship mutual. The friendship, both friend limits and the spent
code are one batch, so simultaneous requests cannot pass a limit or spend a code
twice. Case, the dash and spaces do not matter. It answers `{"id": 41}`, the id
of the friendship for the caller. It refuses with:

| Status | `reason`          | When                                             |
| ------ | ----------------- | ------------------------------------------------ |
| 400    | `bad_request`     | The body has no `code` of 10 letters and digits. |
| 400    | `own_code`        | The code is the caller's.                        |
| 404    | `invite_unknown`  | No such code.                                    |
| 410    | `invite_used`     | Someone already spent it.                        |
| 410    | `invite_expired`  | It is past its 7 days.                           |
| 409    | `already_friends` | They are friends already.                        |
| 409    | `friend_limit`    | Either side has `MAX_FRIENDS` friends.           |

A refusal leaves the code unspent. The daily cleanup deletes expired codes, and
then they answer `invite_unknown`.

`GET /api/friends` lists the friends of the caller:

```json
{ "friends": [{ "id": 41, "streak": 3, "today": true, "xp": 120 }] }
```

`id` is the caller's id for that friendship; each side of a friendship has its
own, and `DELETE /api/friends/41` removes both sides. An id that is not the
caller's answers 404. `streak` is the friend's current streak and `today`
whether they have XP on their own current day. `xp` is their XP in the caller's
ISO week. A friend's list entry has no email, no provider identifier and no
account id, and the account stores no name.

## Weekly board

`GET /api/board` ranks the caller and their friends by XP in the current ISO
week. The week runs from Monday 00:00 to the next Monday 00:00 in the caller's
time zone, for everybody on the board.

```json
{
  "weekStart": "2026-10-19",
  "entries": [
    { "rank": 1, "you": false, "id": 41, "xp": 120 },
    { "rank": 2, "you": true, "id": null, "xp": 85 }
  ]
}
```

Entries are sorted by `xp`, highest first. Equal `xp` share the lowest rank; the
caller comes first among them, then friends in the order they were made. `id` is
the friendship id of `GET /api/friends`, and `null` for the caller.

## On the site

[`site/account.ts`](../site/account.ts) is the client. It puts the _Entrar_ menu
in the header of the catalog, the path pages, the lessons and the privacy page
(`/privacidad.html`), which says what is stored, for how long and how to delete
it.

- Without an account, the page makes no request to `/api` or `/auth`. What it
  looks at to know is the `rising:cuenta` mark in `localStorage`. The editor of
  an exercise that runs in the container asks for the account instead of calling
  `/run` ([protection.md](protection.md#session)).
- _Entrar con Google_ and _Entrar con GitHub_ go to `/auth/<provider>` with
  `return` equal to the current page plus `#cuenta`. On return, that `#cuenta`
  makes the page leave the mark and merge the progress.
- With the mark, each load sends all the browser's progress to `POST /api/merge`
  and stores the response before the page reads it. It waits 4 seconds at most;
  if the Worker does not respond, the page continues with the local data. The
  first time you sign in, that same call merges what was already in the browser
  with the account's data.
- On the first load of a browser that has progress from before each course had
  its own keys, the page moves it to the course before the first sync
  ([architecture.md](architecture.md#progress-in-the-browser)).
- Each change is sent afterwards, in `PUT /api/progress`, 1.5 seconds after the
  last one and always when the page is closed or hidden. Without a network, the
  change stays in `localStorage` and the next load merges it.
- Each `<course>:exercise:<id>` carries `at`, the time of the last edit of the
  code. It changes only when the code changes, so the most recent copy wins when
  merging.
- The synced data are the finished lessons, the code, hints and checks of each
  exercise and the `kv` keys of the table. The text of the reflections
  (`<course>:reflect`) does not leave the browser. A value that the Worker would
  reject (a code of more than 20 000 bytes, for example) is left out of the
  body, because it would reject the whole body.
- The friends page (`/amigos/`) is where the account's numbers show. The XP
  count in the header of every page of the app links to it. Signed in, it shows
  the streak and the reminder opt-in, and the board of
  [Weekly board](#weekly-board) with the time left in the week. The invitation
  link it creates is `/amigos/?c=<code>`: _Compartir enlace_ hands it to the Web
  Share API, and _Copiar enlace_ writes it to the clipboard when the browser has
  no share sheet. Opening a link signed out offers _Entrar_ first, and returns
  to the same link. Each friend row shows the streak and whether they practiced
  today, and _Quitar_ asks to confirm before it calls `DELETE /api/friends/:id`.
  With no friends the board is replaced by the invite action. Friends have no
  names: the page numbers them _Amigo 1_, _Amigo 2_ in the order they were made,
  and keeps the numbers in `rising:amigos`.
- _Cerrar sesión_ calls `POST /auth/logout` and _Borrar mi cuenta_, after a
  confirmation, `DELETE /api/me`. Neither touches what is in the browser. A 401
  response removes the mark.

The local progress passes to the account that signs in, whichever it is. On a
shared machine, whoever signs in afterwards merges what the previous user of the
browser left.

## Data stored

The Worker stores no email, name, avatar or password: it does not request them
from the provider and discards what the provider returns. The schema is
[`src/schema.sql`](../runner/worker/src/schema.sql), which creates a database
that does not exist yet. A live database is altered in place, never recreated:
[deploy.md](deploy.md#update-a-live-database) lists the statements. Everything
hangs from `users` with `ON DELETE CASCADE`.

| Table                | What it stores                                                                                                                           |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `users`              | A random id, the sign-up day, the day of the last visit, the progress version, the time zone and the last local day a reminder went out. |
| `identities`         | Provider and provider identifier of each user.                                                                                           |
| `sessions`           | The SHA-256 hash of a `qg_auth` or CLI token, its expiry and its `kind`. Never the token.                                                |
| `device_codes`       | The hashes of a pending CLI login's two codes, its expiry, its last poll and the decision.                                               |
| `lesson_done`        | The finished lessons and when.                                                                                                           |
| `exercise_state`     | The code, hints, checks and whether it passed, per exercise.                                                                             |
| `kv`                 | The `localStorage` keys of the table above.                                                                                              |
| `attempts`           | One row per run.                                                                                                                         |
| `xp_events`          | One row per XP granted: source, ref, amount and the UTC day. Deleted after 14 days.                                                      |
| `streaks`            | One row per user: the run, the longest run, the freezes held and the last local day with XP.                                             |
| `friendships`        | Two rows per friendship, one for each side, each with its own id.                                                                        |
| `friend_invites`     | The hash of each invite code, its expiry and when it was spent.                                                                          |
| `push_subscriptions` | The push service address, the two keys of a browser's subscription and when it was made.                                                 |

A visit is a request with a session to `/run` or `/api`, or the OAuth return. It
raises `seen_day` at most once a day.

Each 200 response of `/run` writes a row to `attempts`, from the JSON the
container returned, which is what grades the code. The row carries the moment,
the `user_id`, the exercise, the mode, the result (`pass`, `fail`, `error` or
`timeout`), the names of the cases that failed, the name of the Python exception
(or `other`, or `killed_memory`, `killed_disk`, `killed_output` or
`killed_scan`), `ms` and the size of the code in bytes. It does not carry the
code, `stdout`, the error text or the `message` of a case, which could repeat
what the learner wrote. A run is recorded only with `mode` `run` or `check` and
an `exercise` shaped like an exercise id. A failure to write the row is logged
and the response does not change. A row is not modified after it is written.

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

Two crons call the Worker's `scheduled` handler. The hourly one sends the
[streak reminder](#streak-reminder). The daily one (`17 3 * * *`, UTC) deletes
in a single batch the expired attempts, the XP events older than 14 days (the
weekly board and the once-per-day rule read nothing older; streaks live in their
own table), the expired sessions (of both kinds), the expired CLI login codes,
the expired friend invites and the inactive accounts, in that order. Deleting an
account takes everything of theirs with it, subscriptions included.

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
