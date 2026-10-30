// A freeze is earned for every 7 days of a streak, and at most 2 are held.
const FREEZE_EVERY = 7;
const MAX_FREEZES = 2;

export interface Streak {
  current: number;
  longest: number;
  // Whether the user earned XP on `today`.
  today: boolean;
}

// The row of `streaks`.
export interface StreakRow {
  run: number;
  freezes: number;
  longest: number;
  last_day: number;
}

// Folds a local day with XP into the user's row. `?1` is the user, `?2` the
// day. It runs only when the previous statement of the batch stored XP
// (`changes()`). A day not after `last_day` is
// ignored. A gap longer than the held freezes ends the run and drops them.
const REACHED = `CASE WHEN excluded.last_day - streaks.last_day - 1 > streaks.freezes
  THEN 1 ELSE streaks.run + 1 END`;
export const FOLD_DAY = `
INSERT INTO streaks (user_id, run, longest, freezes, last_day)
SELECT ?1, 1, 1, 0, ?2 WHERE changes() > 0
ON CONFLICT (user_id) DO UPDATE SET
  run = ${REACHED},
  freezes = MIN(${MAX_FREEZES},
    CASE WHEN excluded.last_day - streaks.last_day - 1 > streaks.freezes
      THEN 0
      ELSE streaks.freezes - (excluded.last_day - streaks.last_day - 1) END
    + ((${REACHED}) % ${FREEZE_EVERY} = 0)),
  longest = MAX(streaks.longest, ${REACHED}),
  last_day = excluded.last_day
WHERE excluded.last_day > streaks.last_day`;

// `today` is the user's current local day. A gap that remains open today
// counts toward `current` while a freeze covers it.
export function streakOf(row: StreakRow | undefined, today: number): Streak {
  if (!row) return { current: 0, longest: 0, today: false };
  const { run, freezes, longest, last_day: last } = row;
  if (last >= today) return { current: run, longest, today: true };
  return {
    current: today - last - 1 <= freezes ? run : 0,
    longest,
    today: false,
  };
}
