// Optional account to carry progress to another browser (docs/accounts.md).
// Without an account it makes no account requests. With the rising:cuenta mark, it
// merges the progress before painting and sends the changes the Worker accepts.
// The reflections (<course>:reflect) never leave the browser.
import {
  ACCOUNT_EVENT,
  courseKey,
  dayOf,
  appendXpQueue,
  claimAnonymousXp,
  discardStaleReviews,
  lessonOwners,
  migrate,
  migratePreferences,
  PREF,
  read as readKey,
  readJson,
  readXp,
  readXpQueue,
  samePost,
  type XpPost,
  type XpSource,
  write as writeKey,
  writeXpQueue,
} from "./progress.ts";

const FLAG = PREF.account;
const XP_PER_POST = 50;
const RETURN_HASH = "#cuenta";
const SYNC_TIMEOUT_MS = 4000;
const PUSH_DELAY_MS = 1500;
const MAX_CODE_BYTES = 20000;

const LESSON = /^[a-z0-9][a-z0-9-]{0,59}$/;
const COURSE = "[a-z0-9-]{1,40}";
const DONE = new RegExp(`^(${COURSE}):done$`);
const EXERCISE = new RegExp(
  `^${COURSE}:exercise:([a-z0-9-]{1,40}/[a-z0-9-]{1,40})$`,
);
const KV = new RegExp(
  `^${COURSE}:(?:pos:[a-z0-9-]{1,60}|heard:[a-z0-9-]{1,60}|predict:[a-z0-9-]{1,60}:[A-Za-z0-9_-]{1,60}|hitos|repaso)$`,
);

// The body of POST /api/merge and PUT /api/progress, and the merge response.
interface ExerciseBody {
  hints: number;
  checks: number;
  passed: boolean;
  at: number;
  code?: string;
}
interface Progress {
  done: string[];
  exercises: Record<string, ExerciseBody>;
  kv: Record<string, unknown>;
}

const read = readKey;
const write = writeKey;
const parse = (raw: string | null): unknown => {
  try {
    return JSON.parse(raw as string);
  } catch {
    return undefined;
  }
};
const count = (n: unknown) =>
  typeof n === "number" && Number.isSafeInteger(n) && n >= 0 ? n : 0;

const listeners = new Set<() => void>();
const state = { signedIn: read(FLAG) !== null, busy: false, message: "" };
const update = (patch: Partial<typeof state>) => {
  Object.assign(state, patch);
  listeners.forEach((f) => f());
};
// The XP queue of the account stays under its own key, for its next sign-in.
const forget = () => {
  try {
    localStorage.removeItem(FLAG);
    localStorage.removeItem(PREF.tally);
  } catch {}
  update({ signedIn: false });
  dispatchEvent(new Event(ACCOUNT_EVENT));
};

function exerciseBody(raw: unknown): ExerciseBody | null {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw))
    return null;
  const value = raw as Record<string, unknown>;
  const out: ExerciseBody = {
    hints: count(value.hints),
    checks: count(value.checks),
    passed: value.passed === true,
    at: count(value.at),
  };
  if (
    typeof value.code === "string" &&
    new Blob([value.code]).size <= MAX_CODE_BYTES
  )
    out.code = value.code;
  return out;
}

// Skip values that would make the whole body of POST /api/merge fail.
function collect(keys: Iterable<string>): Progress {
  const body: Progress = { done: [], exercises: {}, kv: {} };
  for (const key of keys) {
    const value = parse(read(key));
    if (value === undefined) continue;
    const exercise = EXERCISE.exec(key);
    if (DONE.test(key)) {
      if (Array.isArray(value))
        body.done.push(
          ...value.filter(
            (id): id is string => typeof id === "string" && LESSON.test(id),
          ),
        );
    } else if (exercise) {
      const item = exerciseBody(value);
      if (item) body.exercises[exercise[1]] = item;
    } else if (KV.test(key)) {
      body.kv[key] = value;
    }
  }
  return body;
}

const allKeys = () => {
  const keys: string[] = [];
  try {
    for (let k = 0; k < localStorage.length; k++) {
      const key = localStorage.key(k);
      if (key !== null) keys.push(key);
    }
  } catch {}
  return keys;
};

// The response includes what was sent and replaces the local values. Each lesson's done state
// and exercises go to the course that owns the lesson.
async function adopt(progress: Progress) {
  const owner =
    progress.done.length || Object.keys(progress.exercises).length
      ? await lessonOwners()
      : new Map<string, string>();
  const byCourse = new Map<string, Set<string>>();
  for (const lesson of progress.done) {
    const course = owner.get(lesson);
    if (course === undefined) continue;
    const key = courseKey(course, "done");
    if (!byCourse.has(key))
      byCourse.set(key, new Set(readJson<string[]>(key, [])));
    byCourse.get(key)!.add(lesson);
  }
  for (const [key, done] of byCourse) write(key, JSON.stringify([...done]));
  for (const [id, item] of Object.entries(progress.exercises)) {
    const course = owner.get(id.split("/")[0]);
    if (course === undefined) continue;
    const key = courseKey(course, `exercise:${id}`);
    const local = (parse(read(key)) as Partial<ExerciseBody> | null) || {};
    write(
      key,
      JSON.stringify({ ...local, ...item, code: item.code ?? local.code }),
    );
  }
  for (const [key, value] of Object.entries(progress.kv))
    write(key, JSON.stringify(value));
}

const api = (
  method: string,
  path: string,
  body?: unknown,
  options: RequestInit = {},
) =>
  fetch(path, {
    method,
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    ...options,
  });

// 401: the session expired or was closed elsewhere.
const lapsed = (resp: Response) => {
  if (resp.status !== 401) return false;
  forget();
  return true;
};

async function sync() {
  const ctl = new AbortController();
  const cut = setTimeout(() => ctl.abort(), SYNC_TIMEOUT_MS);
  try {
    const resp = await api("POST", "/api/merge", collect(allKeys()), {
      signal: ctl.signal,
    });
    if (lapsed(resp)) return;
    if (!resp.ok) throw new Error(String(resp.status));
    const reply = (await resp.json()) as {
      progress: Progress;
      account: string;
    };
    write(FLAG, reply.account);
    await adopt(reply.progress);
    update({ signedIn: true, message: "" });
  } catch {
    update({
      message: "No se pudo sincronizar. Tu progreso sigue en este navegador.",
    });
  } finally {
    clearTimeout(cut);
  }
}

const dirty = new Set<string>();
let timer: ReturnType<typeof setTimeout> | undefined,
  pushing = Promise.resolve();
function flush({ unloading = false }: { unloading?: boolean } = {}) {
  clearTimeout(timer);
  timer = undefined;
  if (!state.signedIn || !dirty.size) return;
  const body = collect(dirty);
  dirty.clear();
  pushing = pushing.then(async () => {
    try {
      const resp = await api("PUT", "/api/progress", body, {
        keepalive: unloading,
      });
      if (!lapsed(resp) && !resp.ok) throw new Error(String(resp.status));
    } catch {
      update({
        message: "No se pudo guardar en tu cuenta. Se reintentará al volver.",
      });
    }
  });
}
function changed(key: string) {
  if (
    !state.signedIn ||
    !(DONE.test(key) || EXERCISE.test(key) || KV.test(key))
  )
    return;
  dirty.add(key);
  clearTimeout(timer);
  timer = setTimeout(flush, PUSH_DELAY_MS);
}
addEventListener("pagehide", () => flush({ unloading: true }));
addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flush({ unloading: true });
});

const announce = () => dispatchEvent(new Event(ACCOUNT_EVENT));

// The streak and the XP of today, as the account counts them, for the header.
async function refreshTally(): Promise<void> {
  if (!state.signedIn) return;
  try {
    const [streakReply, xpReply] = await Promise.all([
      api("GET", "/api/streak"),
      api("GET", "/api/xp"),
    ]);
    if (lapsed(streakReply) || lapsed(xpReply)) return;
    if (!streakReply.ok || !xpReply.ok) return;
    const now = (await streakReply.json()) as {
      current: number;
      today: boolean;
    };
    const day = (await xpReply.json()) as { today: number };
    write(
      PREF.tally,
      JSON.stringify({
        streak: now.current,
        earned: now.today,
        xp: day.today,
        day: dayOf(new Date()),
      }),
    );
    announce();
  } catch {}
}

// A refusal other than 401, 429 or a server error cannot succeed on a second try, so the post is dropped.
let sending = false;
async function drainXp(): Promise<void> {
  const owner = read(FLAG);
  if (!state.signedIn || owner === null) return;
  const head = readXpQueue(owner)[0];
  if (!head) return;
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  let resp: Response;
  try {
    resp = await api("POST", "/api/xp", { ...head, tz });
  } catch {
    return;
  }
  if (lapsed(resp) || resp.status === 429 || resp.status >= 500) return;
  writeXpQueue(
    owner,
    readXpQueue(owner).filter((post) => !samePost(post, head)),
  );
  return drainXp();
}
// A call that arrives while a send runs (the connection returning, for one) asks for another pass,
// because the running one may have read the queue before the connection came back.
let again = false;
async function sendXp(): Promise<void> {
  if (sending) {
    again = true;
    return;
  }
  sending = true;
  try {
    await drainXp();
  } finally {
    sending = false;
  }
  if (again) {
    again = false;
    return sendXp();
  }
  await refreshTally();
}

// Queues XP in the queue of the signed-in account and sends it now, or when the connection returns.
// Without an account there is nothing to send. A resend is safe: the account takes one award per
// source and ref each day, the day being the one in `earnedAt`, which the queue keeps, so a resend
// after midnight is the same award.
function xp(source: XpSource, ref: string, amount: number) {
  const owner = read(FLAG);
  if (!state.signedIn || owner === null) return;
  const queue = readXpQueue(owner);
  const post = { source, ref, amount, earnedAt: Date.now() };
  const queued = queue.find((p) => samePost(p, post));
  writeXpQueue(owner, [
    ...queue.filter((p) => p !== queued),
    { ...post, earnedAt: queued?.earnedAt ?? post.earnedAt },
  ]);
  announce();
  void sendXp();
}

// The first time an account signs in on this device, the XP the browser already holds for today
// joins the queue of XP earned before any account. The log keeps days, not moments, so earlier days
// cannot be dated and are not sent.
function seedXp() {
  if (read(PREF.xpSeeded) !== null) return;
  write(PREF.xpSeeded, "1");
  const day = dayOf(new Date());
  let rest = readXp()[day] ?? 0;
  const chunks: XpPost[] = [];
  for (let k = 0; rest > 0; k++) {
    const amount = Math.min(rest, XP_PER_POST);
    chunks.push({
      source: "drill",
      ref: `local:${day}:${k}`,
      amount,
      earnedAt: Date.now(),
    });
    rest -= amount;
  }
  appendXpQueue(null, chunks);
}
addEventListener("online", () => void sendXp());

const signInHref = (provider: string) => {
  const back = location.pathname + location.search + RETURN_HASH;
  return `/auth/${provider}?return=${encodeURIComponent(back)}`;
};
const signIn = (provider: string) => {
  location.href = signInHref(provider);
};
async function signOut() {
  flush();
  await pushing;
  await sendXp();
  try {
    const resp = await api("POST", "/auth/logout");
    if (!resp.ok) throw new Error(String(resp.status));
    forget();
  } catch {
    update({ message: "No se pudo cerrar la sesión. Inténtalo de nuevo." });
  }
}
// Delete the account and what it stores. The copy in this browser stays.
async function deleteAccount() {
  clearTimeout(timer);
  dirty.clear();
  await pushing;
  try {
    const resp = await api("DELETE", "/api/me");
    if (!resp.ok && !lapsed(resp)) throw new Error(String(resp.status));
    forget();
    update({
      message: "Cuenta borrada. Tu progreso sigue en este navegador.",
    });
  } catch {
    update({ message: "No se pudo borrar la cuenta. Inténtalo de nuevo." });
  }
}

function mount(host: HTMLElement) {
  host.classList.add("acct");
  const button = document.createElement("button");
  button.type = "button";
  button.setAttribute("aria-haspopup", "true");
  button.setAttribute("aria-expanded", "false");
  const menu = document.createElement("div");
  menu.className = "acct-menu";
  menu.hidden = true;
  host.append(button, menu);
  let confirming = false;

  const item = (label: string, onclick: () => unknown, cls = "") => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = cls;
    b.textContent = label;
    b.addEventListener("click", onclick);
    menu.append(b);
  };
  const para = (text: string) => {
    const p = document.createElement("p");
    p.textContent = text;
    menu.append(p);
  };
  const privacy = () => {
    const a = document.createElement("a");
    a.href = "/privacidad.html";
    a.textContent = "Privacidad";
    menu.append(a);
  };
  const close = () => {
    menu.hidden = true;
    button.setAttribute("aria-expanded", "false");
    confirming = false;
    paint();
  };

  function paint() {
    button.textContent = state.signedIn ? "Cuenta ✓" : "Entrar";
    button.title = state.signedIn
      ? "Tu progreso se guarda en tu cuenta"
      : "Guarda tu progreso y llévalo a otro navegador";
    menu.textContent = "";
    if (state.message) para(state.message);
    if (!state.signedIn) {
      para(
        "Entra para guardar tu progreso en una cuenta y verlo en otro navegador. Es opcional.",
      );
      item("Entrar con Google", () => signIn("google"));
      item("Entrar con GitHub", () => signIn("github"));
    } else if (confirming) {
      para(
        "Se borra tu cuenta y todo lo que guarda. Lo que hay en este navegador se queda.",
      );
      item(
        "Sí, borrar",
        async () => {
          confirming = false;
          await deleteAccount();
        },
        "danger",
      );
      item(
        "Cancelar",
        () => {
          confirming = false;
          paint();
        },
        "cancel",
      );
    } else {
      item("Cerrar sesión", signOut);
      item(
        "Borrar mi cuenta",
        () => {
          confirming = true;
          paint();
          menu.querySelector<HTMLElement>(".cancel")!.focus();
        },
        "danger",
      );
    }
    privacy();
  }

  button.addEventListener("click", () => {
    menu.hidden = !menu.hidden;
    button.setAttribute("aria-expanded", String(!menu.hidden));
    if (menu.hidden) close();
  });
  // The menu keys are not lesson shortcuts.
  host.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !menu.hidden) {
      close();
      button.focus();
    }
    e.stopPropagation();
  });
  // In the capture phase: a click on a menu item repaints it, so the item would be outside `host` by the time the event got here.
  document.addEventListener(
    "click",
    (e) => {
      if (!menu.hidden && !host.contains(e.target as Node)) close();
    },
    true,
  );
  listeners.add(paint);
  paint();
}
addEventListener("DOMContentLoaded", () =>
  document.querySelectorAll<HTMLElement>("[data-account]").forEach(mount),
);

// With the mark, or on return from the provider, the progress is merged before the page reads it.
const returning = location.hash === RETURN_HASH;
if (returning)
  history.replaceState(null, "", location.pathname + location.search);
// Migrate legacy keys before syncing so each value is sent from its course namespace once.
migratePreferences();
discardStaleReviews();
const migrated = (async () => {
  if (readKey("rising:migrated") !== null) return;
  try {
    const owner = await lessonOwners();
    const courses: Record<string, string[]> = {};
    for (const [lesson, course] of owner) (courses[course] ??= []).push(lesson);
    migrate(courses);
  } catch {}
})();
const ready = migrated.then(() =>
  state.signedIn || returning ? sync() : undefined,
);

void ready.then(() => {
  const owner = read(FLAG);
  if (state.signedIn && owner !== null) {
    seedXp();
    claimAnonymousXp(owner);
  }
  return sendXp();
});

// A request to the account for the pages that show it. A 401 ends the sign-in here, so every page
// sees the same state.
async function request(method: string, path: string, body?: unknown) {
  const resp = await api(method, path, body);
  lapsed(resp);
  return resp;
}

window.QGAccount = {
  ready,
  changed,
  mount,
  xp,
  request,
  signInHref,
  signedIn: () => state.signedIn,
  lapsed,
};
