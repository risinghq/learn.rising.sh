// Where a learner's progress lives in localStorage, shared by the shell, the player and the account.
//
// A course writes under its own slug: `<course>:done`, `<course>:pos:<lesson>`,
// `<course>:exercise:<lesson>/<name>` and so on. Preferences and the XP record belong to
// no course and use the `rising:` prefix. Legacy `qiskit:` keys are migrated by the account
// and player entry points.

const LEGACY = "qiskit";
const MIGRATED = "rising:migrated";

export const PREF = {
  theme: "rising:theme",
  speed: "rising:speed",
  mute: "rising:mute",
  account: "rising:cuenta",
  xp: "rising:xp",
  /** The course whose lesson the learner opened last. */
  last: "rising:last",
  /** The XP of finished drill sessions that the account has not received yet. */
  xpQueue: "rising:xpq",
} as const;

/** The keys of a lesson, which end with its id (and a step for `predict` and `reflect`). */
const LESSON_KEY =
  /^(pos|heard|predict|reflect):([a-z0-9][a-z0-9-]{0,59})(?::.+)?$/;
const EXERCISE_KEY = /^exercise:([a-z0-9][a-z0-9-]{0,59})\/[a-z0-9-]{1,40}$/;

export const XP_PER_LESSON = 10;
const XP_DAYS = 400;
const DAY_MS = 864e5;

export const read = (key: string): string | null => {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
};
export const write = (key: string, value: string) => {
  try {
    localStorage.setItem(key, value);
  } catch {}
};
const remove = (key: string) => {
  try {
    localStorage.removeItem(key);
  } catch {}
};
export const readJson = <T>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
};
const storedKeys = () => {
  const keys: string[] = [];
  try {
    for (let k = 0; k < localStorage.length; k++) {
      const key = localStorage.key(k);
      if (key !== null) keys.push(key);
    }
  } catch {}
  return keys;
};
const ids = (value: unknown): string[] =>
  Array.isArray(value)
    ? value.filter((id): id is string => typeof id === "string")
    : [];

/** The course a page belongs to: the first segment of its path, as in `/qiskit/lesson.html`. */
export const courseOf = (pathname: string) => pathname.split("/")[1] ?? "";

/** The key of a course's own data: `done`, `hitos`, `pos:<lesson>`. */
export const courseKey = (course: string, name: string) => `${course}:${name}`;

/** Moves legacy `qiskit:` keys to the course that owns each lesson. */
export function migratePreferences() {
  for (const [name, key] of [
    ["theme", PREF.theme],
    ["speed", PREF.speed],
    ["mute", PREF.mute],
    ["cuenta", PREF.account],
  ]) {
    const old = read(`${LEGACY}:${name}`);
    if (old === null) continue;
    if (read(key) === null) write(key, old);
    remove(`${LEGACY}:${name}`);
  }
}

/** Moves one lesson's keys to its course. */
export function migrateLesson(course: string, lesson: string) {
  migrateAll(new Map([[lesson, course]]));
}

function migrateAll(owner: Map<string, string>) {
  for (const key of storedKeys()) {
    if (!key.startsWith(`${LEGACY}:`)) continue;
    const rest = key.slice(LEGACY.length + 1);
    const lesson = LESSON_KEY.exec(rest)?.[2] ?? EXERCISE_KEY.exec(rest)?.[1];
    const course = lesson === undefined ? undefined : owner.get(lesson);
    if (course === undefined || course === LEGACY) continue;
    const target = courseKey(course, rest);
    const value = read(key);
    if (value !== null && read(target) === null) write(target, value);
    remove(key);
  }
}

/**
 * Splits the lessons done and the lesson keys of the old `qiskit:` namespace between the courses.
 * `courses` maps each slug to its lesson ids. It runs once per browser.
 */
export function migrate(courses: Record<string, string[]>) {
  if (read(MIGRATED) !== null) return;
  const legacyDone = ids(readJson<unknown>(courseKey(LEGACY, "done"), []));
  const owner = new Map<string, string>();
  for (const [slug, lessons] of Object.entries(courses))
    for (const lesson of lessons) owner.set(lesson, slug);
  migrateAll(owner);
  for (const [slug, lessons] of Object.entries(courses)) {
    const own = new Set(lessons);
    const stored =
      slug === LEGACY
        ? []
        : ids(readJson<unknown>(courseKey(slug, "done"), []));
    const done = new Set(
      [...stored, ...legacyDone].filter((id) => own.has(id)),
    );
    if (done.size || read(courseKey(slug, "done")) !== null)
      write(courseKey(slug, "done"), JSON.stringify([...done]));
  }
  write(MIGRATED, "1");
}

/** The lessons a learner finished in a course. */
export const doneOf = (course: string): string[] =>
  ids(readJson<unknown>(courseKey(course, "done"), []));

/** Marks a lesson done and, the first time, awards its XP. */
export function completeLesson(course: string, lesson: string): boolean {
  const done = new Set(doneOf(course));
  const first = !done.has(lesson);
  done.add(lesson);
  write(courseKey(course, "done"), JSON.stringify([...done]));
  if (first) addXp(XP_PER_LESSON);
  return first;
}

/** Returns the local calendar day in `YYYY-MM-DD` form. */
export const dayOf = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;

export type XpLog = Record<string, number>;

export const readXp = (): XpLog => {
  const log = readJson<unknown>(PREF.xp, {});
  return typeof log === "object" && log !== null && !Array.isArray(log)
    ? (log as XpLog)
    : {};
};

export function addXp(amount: number, now = new Date()) {
  const log = readXp();
  const today = dayOf(now);
  log[today] = (log[today] ?? 0) + amount;
  const days = Object.keys(log).toSorted();
  for (const day of days.slice(0, Math.max(0, days.length - XP_DAYS)))
    delete log[day];
  write(PREF.xp, JSON.stringify(log));
}

/** XP earned on `now`'s day and the days in a row that earned some, counting yesterday as alive. */
export function xpSummary(log: XpLog, now = new Date()) {
  let day = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 12);
  const today = log[dayOf(day)] ?? 0;
  if (today === 0) day = new Date(day.getTime() - DAY_MS);
  let streak = 0;
  while ((log[dayOf(day)] ?? 0) > 0) {
    streak++;
    day = new Date(day.getTime() - DAY_MS);
  }
  return { today, streak };
}

/** One recorded answer to a drill item. `at` is in Unix milliseconds. */
export interface Review {
  item: string;
  at: number;
  correct: boolean;
}

export const reviewKey = (course: string) => courseKey(course, "repaso");

const MAX_REVIEWS = 800;
const REVIEWS_PER_ITEM = 4;

const isReview = (value: unknown): value is Review => {
  const r = value as Review | null;
  return (
    typeof r === "object" &&
    r !== null &&
    typeof r.item === "string" &&
    Number.isSafeInteger(r.at) &&
    typeof r.correct === "boolean"
  );
};

/**
 * The answers in a stored review log, or undefined when the value has another shape, such as the
 * boxes an earlier version kept there.
 */
export const reviewsOf = (value: unknown): Review[] | undefined =>
  Array.isArray(value)
    ? value
        .filter(isReview)
        .map(({ item, at, correct }) => ({ item, at, correct }))
    : undefined;

/** The answers a learner gave in a course. Anything stored in another shape is ignored. */
export const readReviews = (course: string): Review[] =>
  reviewsOf(readJson<unknown>(reviewKey(course), [])) ?? [];

/**
 * Removes a review log in the shape of an earlier version, the Leitner boxes `{id: {box, due}}`.
 * They do not map onto the answers, and the account rejects a body that carries them.
 */
export function discardStaleReviews() {
  for (const key of storedKeys()) {
    if (
      key.endsWith(":repaso") &&
      reviewsOf(readJson<unknown>(key, [])) === undefined
    )
      remove(key);
  }
}

/**
 * Keeps the last answers of each item and the latest overall, so the log stays under the size the
 * account accepts. The scheduler replays what is left.
 */
export function compactReviews(log: Review[]): Review[] {
  const seen = new Map<string, number>();
  const kept: Review[] = [];
  for (const review of log.toSorted((a, b) => b.at - a.at)) {
    const count = seen.get(review.item) ?? 0;
    if (count >= REVIEWS_PER_ITEM) continue;
    seen.set(review.item, count + 1);
    kept.push(review);
  }
  return kept.slice(0, MAX_REVIEWS).toReversed();
}

/** The XP of one session, which the account receives once the connection allows. */
export interface XpPost {
  ref: string;
  amount: number;
}

export const readXpQueue = (): XpPost[] => {
  const queue = readJson<unknown>(PREF.xpQueue, []);
  return Array.isArray(queue)
    ? queue.filter(
        (post): post is XpPost =>
          typeof post?.ref === "string" && Number.isInteger(post.amount),
      )
    : [];
};
export const writeXpQueue = (queue: XpPost[]) =>
  queue.length
    ? write(PREF.xpQueue, JSON.stringify(queue))
    : remove(PREF.xpQueue);

interface CourseIndex {
  parts: { lessons: { id: string }[] }[];
}

async function get<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`${url}: ${resp.status}`);
  return (await resp.json()) as T;
}

/** Which course owns each lesson, read from the published indexes. */
export async function lessonOwners(): Promise<Map<string, string>> {
  const courses = await get<{ slug: string }[]>("/courses.json");
  const owner = new Map<string, string>();
  const indexes = await Promise.all(
    courses.map((c) =>
      get<CourseIndex>(`/${c.slug}/course.json`).then((index) => ({
        c,
        index,
      })),
    ),
  );
  for (const { c, index } of indexes)
    for (const part of index.parts)
      for (const l of part.lessons) owner.set(l.id, c.slug);
  return owner;
}
