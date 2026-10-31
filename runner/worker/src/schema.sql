-- Schema of the D1 database (binding DB). There are no migrations: to change it,
-- drop the database, create another and apply this file. D1 enforces foreign
-- keys, so deleting a row of users deletes everything of that user.
-- No email, name, avatar or password is stored.
-- Times: *_day are days since the epoch; exercise_state.updated_at is in
-- milliseconds (the `at` the page sends); the rest are Unix seconds.

CREATE TABLE users (
  id          TEXT PRIMARY KEY,
  created_day INTEGER NOT NULL,
  seen_day    INTEGER NOT NULL,
  -- Rises with each progress write. A write counts only if the version is
  -- still the one it read (see mergeProgress).
  progress_version INTEGER NOT NULL DEFAULT 0,
  -- IANA name that the page sends with its XP. It sets the day of a streak and
  -- the start of the week on the board.
  time_zone   TEXT NOT NULL DEFAULT 'UTC',
  -- The last local day (in `time_zone`) on which the streak reminder went out.
  reminded_day INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE identities (
  provider TEXT NOT NULL CHECK (provider IN ('google', 'github')),
  subject  TEXT NOT NULL,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (provider, subject)
) WITHOUT ROWID;

-- `kind` separates web tokens in the `qg_auth` cookie from CLI tokens in an
-- `Authorization: Bearer` header. Each transport accepts only its own kind.
CREATE TABLE sessions (
  token_hash TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL,
  kind       TEXT NOT NULL DEFAULT 'web' CHECK (kind IN ('web', 'cli'))
) WITHOUT ROWID;

CREATE TABLE lesson_done (
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  lesson  TEXT NOT NULL,
  done_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, lesson)
) WITHOUT ROWID;

CREATE TABLE exercise_state (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  exercise   TEXT NOT NULL,
  code       TEXT,
  hints      INTEGER NOT NULL DEFAULT 0,
  checks     INTEGER NOT NULL DEFAULT 0,
  -- The server sets this only after a passing check for the user.
  passed     INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, exercise)
) WITHOUT ROWID;

CREATE TABLE kv (
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key        TEXT NOT NULL,
  value      TEXT NOT NULL,
  updated_at INTEGER NOT NULL,
  PRIMARY KEY (user_id, key)
) WITHOUT ROWID;

CREATE TABLE attempts (
  id         INTEGER PRIMARY KEY,
  at         INTEGER NOT NULL,
  user_id    TEXT REFERENCES users(id) ON DELETE CASCADE,
  exercise   TEXT NOT NULL CHECK (exercise GLOB '[a-z0-9-]*/[a-z0-9-]*'),
  mode       TEXT NOT NULL CHECK (mode IN ('run', 'check')),
  outcome    TEXT NOT NULL CHECK (outcome IN ('pass', 'fail', 'error', 'timeout')),
  failed     TEXT NOT NULL DEFAULT '[]',
  error_kind TEXT,
  hints      INTEGER NOT NULL DEFAULT 0,
  ms         INTEGER NOT NULL,
  code_bytes INTEGER NOT NULL
);

CREATE INDEX attempts_exercise ON attempts (exercise, at);
CREATE INDEX attempts_user ON attempts (user_id);
CREATE INDEX attempts_at ON attempts (at);

-- A row records granted XP. `utc_day` enforces the daily cap and uniqueness.
-- The daily purge deletes rows older than two weeks: the weekly board and the
-- once-per-day rule read nothing older.
CREATE TABLE xp_events (
  id        INTEGER PRIMARY KEY,
  user_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  at        INTEGER NOT NULL,
  utc_day   INTEGER NOT NULL,
  source    TEXT NOT NULL CHECK (source IN ('drill', 'exercise', 'browser', 'lesson', 'cli')),
  ref       TEXT NOT NULL,
  amount    INTEGER NOT NULL CHECK (amount > 0)
);

CREATE UNIQUE INDEX xp_ref_day ON xp_events (user_id, utc_day, source, ref);
CREATE INDEX xp_at ON xp_events (user_id, at);

-- The streak of a user folded day by day, so a read never replays history.
-- `run` is the days in the current run, `freezes` the freezes held and
-- `last_day` the last local day with XP.
CREATE TABLE streaks (
  user_id  TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  run      INTEGER NOT NULL,
  longest  INTEGER NOT NULL,
  freezes  INTEGER NOT NULL,
  last_day INTEGER NOT NULL
) WITHOUT ROWID;

-- Each friendship has one row per side. An owner sees only the row's id.
CREATE TABLE friendships (
  id        INTEGER PRIMARY KEY,
  user_id   TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  friend_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  since     INTEGER NOT NULL,
  UNIQUE (user_id, friend_id),
  CHECK (user_id <> friend_id)
);

CREATE INDEX friendships_friend ON friendships (friend_id);

-- Store only the invite hash. `used_at` records the request that spends it.
CREATE TABLE friend_invites (
  code_hash  TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL,
  used_at    INTEGER
) WITHOUT ROWID;

CREATE INDEX friend_invites_user ON friend_invites (user_id);

-- A browser that accepted streak reminders. One endpoint belongs to one user:
-- subscribing again from another account moves it.
CREATE TABLE push_subscriptions (
  endpoint   TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  p256dh     TEXT NOT NULL,
  auth       TEXT NOT NULL,
  created_at INTEGER NOT NULL
) WITHOUT ROWID;

CREATE INDEX push_subscriptions_user ON push_subscriptions (user_id);

-- A device-flow login in progress. The database stores hashes of both codes.
-- `decision` is NULL until the learner answers, and collection deletes the row.
-- `polled_at` is in milliseconds.
CREATE TABLE device_codes (
  device_hash TEXT PRIMARY KEY,
  user_hash   TEXT NOT NULL UNIQUE,
  expires_at  INTEGER NOT NULL,
  polled_at   INTEGER NOT NULL DEFAULT 0,
  user_id     TEXT REFERENCES users(id) ON DELETE CASCADE,
  decision    TEXT CHECK (decision IN ('approved', 'denied'))
) WITHOUT ROWID;
