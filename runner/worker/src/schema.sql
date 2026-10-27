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
  progress_version INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE identities (
  provider TEXT NOT NULL CHECK (provider IN ('google', 'github')),
  subject  TEXT NOT NULL,
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  PRIMARY KEY (provider, subject)
) WITHOUT ROWID;

CREATE TABLE sessions (
  token_hash TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL
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
