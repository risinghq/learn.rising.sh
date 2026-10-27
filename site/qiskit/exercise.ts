// The «exercise» block: a Python editor with Ejecutar, Comprobar, hints and progress (docs/exercises.md).
//
// spec: exercise (id) · prompt · level · hints · starter · cases (names of the visible cases)
// Ejecutar and Comprobar send the code to /run on the same origin as the page.
// The first request of a session may need Turnstile and repeat the request with the token.

// The browser stores the code, the hints seen and the solved state in
// qiskit:exercise:<id>. `at` records the last edit of the code.
// With an account, account.ts also sends that data to the server.
import type { Editor } from "../../editor/src/index.ts";
import { BLOCKS, LEVELS } from "./blocks.ts";
import type { BlockObject } from "./lesson.ts";

interface Turnstile {
  render: (
    container: HTMLElement,
    options: {
      sitekey: string;
      appearance: string;
      callback: (token: string) => void;
      "error-callback": () => void;
    },
  ) => string;
  remove: (id: string) => void;
}
declare global {
  interface Window {
    turnstile: Turnstile;
  }
}

/** What the browser stores under qiskit:exercise:<id>. */
interface Saved {
  code?: string;
  hints?: number;
  checks?: number;
  passed?: boolean;
  at?: number;
}
interface TestResult {
  name: string;
  visible: boolean;
  passed: boolean;
  message?: string;
  hint: number;
}
/** The response of POST /run. */
interface RunReply {
  passed?: boolean;
  error?: string;
  stdout?: string;
  ms?: number | null;
  tests?: TestResult[];
  reason?: string;
  sitekey?: string;
}
type Mode = "run" | "check";

const CALL_TIMEOUT_MS = 30000;
const SLOW_MS = 4000;
const RUN_URL = "/run";
const MOD = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Ctrl";
const HTTP_ERRORS: Record<number, string> = {
  400: "El corredor no entendió la petición.",
  404: "El corredor no conoce este ejercicio.",
  413: "El código es demasiado largo: el máximo es 20 000 bytes.",
  429: "Has ejecutado demasiadas veces seguidas. Espera un momento.",
  503: "El corredor está ocupado. Inténtalo de nuevo en unos segundos.",
};

// Load editor.js only in lessons with an exercise, so other lessons do not download it.
let editorLib: Promise<Window["QGEditor"]> | null = null,
  turnstileLib: Promise<Turnstile> | null = null;
const loadEditor = () =>
  (editorLib ??= new Promise((ok, no) => {
    const sc = document.createElement("script");
    sc.src = "editor.js";
    sc.addEventListener("load", () => ok(window.QGEditor));
    sc.addEventListener("error", () => {
      editorLib = null;
      no(new Error("editor"));
    });
    document.head.appendChild(sc);
  }));
const loadTurnstile = () =>
  (turnstileLib ??= new Promise((ok, no) => {
    const sc = document.createElement("script");
    sc.src =
      "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    sc.addEventListener("load", () => ok(window.turnstile));
    sc.addEventListener("error", () => {
      turnstileLib = null;
      no(new Error("turnstile"));
    });
    document.head.appendChild(sc);
  }));
// The token is used once. The widget appears only if Cloudflare asks for it.
const turnstileToken = async (
  sitekey: string,
  slot: HTMLElement,
  signal: AbortSignal,
) => {
  let id: string | undefined, lib: Turnstile | undefined;
  try {
    const loaded = (lib = await loadTurnstile());
    return await new Promise<string>((ok, no) => {
      signal.addEventListener("abort", () =>
        no(new DOMException("", "AbortError")),
      );
      id = loaded.render(slot, {
        sitekey,
        appearance: "interaction-only",
        callback: ok,
        "error-callback": () => no(new Error("turnstile")),
      });
    });
  } finally {
    if (id !== undefined) lib?.remove(id);
    slot.remove();
  }
};

const progress = {
  get(id: string): Saved {
    try {
      return (
        JSON.parse(localStorage.getItem(`qiskit:exercise:${id}`) ?? "null") ||
        {}
      );
    } catch {
      return {};
    }
  },
  set(id: string, patch: Saved) {
    const key = `qiskit:exercise:${id}`;
    try {
      localStorage.setItem(
        key,
        JSON.stringify({
          ...progress.get(id),
          ...patch,
          ...("code" in patch && { at: Date.now() }),
        }),
      );
    } catch {}
    QGAccount.changed(key);
  },
};
const seconds = (ms: number) => `${(ms / 1000).toFixed(1).replace(".", ",")} s`;

const tally = (tests: TestResult[]) =>
  (
    [
      [true, "visibles"],
      [false, "ocultos"],
    ] as const
  )
    .map(
      ([visible, label]) =>
        [tests.filter((t) => t.visible === visible), label] as const,
    )
    .filter(([group]) => group.length)
    .map(
      ([group, label]) =>
        `${group.filter((t) => t.passed).length} de ${group.length} ${label}`,
    )
    .join(" · ");

BLOCKS.exercise = (box, s, A) => {
  const o: BlockObject = { spec: s };
  const hintList = s.hints ?? [];
  box.classList.remove("fig");
  box.classList.add("xpanel");
  const card = A.el("div", "mcard", box);
  const saved = progress.get(s.exercise);

  const head = A.el("div", "xhead", card);
  A.el("div", "mtitle", head).textContent = "Ejercicio";
  A.el("span", "xlevel", head).textContent = LEVELS[s.level] || LEVELS[1];
  const solved = A.el("span", "xsolved", head);
  solved.textContent = "Resuelto";
  solved.hidden = !saved.passed;
  A.rich(A.el("div", "xprompt", card), s.prompt);

  const grid = A.el("div", "xgrid", card);
  const left = A.el("div", "xleft", grid),
    right = A.el("div", "xright", grid);
  const host = A.el("div", "xeditor", left);
  A.el("pre", "xplaceholder", host).textContent = saved.code ?? s.starter;
  let ed: Editor | null = null;

  const bar = A.el("div", "xbar", left);
  const btn = (label: string, cls: string, fn: () => void, title: string) => {
    const b = A.el("button", "abtn xbtn " + cls, bar);
    b.type = "button";
    b.textContent = label;
    b.title = title;
    b.addEventListener("click", (e) => {
      e.stopPropagation();
      fn();
    });
    return b;
  };
  const runBtn = btn(
    "Ejecutar",
    "",
    () => send("run"),
    `Ejecuta el código (${MOD}+Intro)`,
  );
  const checkBtn = btn(
    "Comprobar",
    "primary",
    () => send("check"),
    `Ejecuta el código y prueba los casos (${MOD}+Mayús+Intro)`,
  );
  A.el("span", "xspace", bar);
  const hintBtn = hintList.length
    ? btn("Pista", "", () => nextHint(), "Muestra la siguiente pista")
    : null;
  btn(
    "Empezar de nuevo",
    "",
    () => {
      ed?.set(s.starter);
      progress.set(s.exercise, { code: s.starter });
      ed?.focus();
    },
    `Vuelve al código inicial. Se puede deshacer con ${MOD}+Z`,
  );
  A.el("p", "xkeys", left).textContent =
    `${MOD}+Intro ejecuta · ${MOD}+Mayús+Intro comprueba · Esc y luego Tab sale del editor`;
  if (s.cases?.length)
    A.el("p", "mhow", left).textContent =
      `Casos visibles: ${s.cases.join(" · ")}. Hay además casos ocultos.`;

  const status = A.el("div", "xstatus", right);
  status.setAttribute("role", "status");
  const out = A.el("div", "xout", right);
  const hints = A.el("div", "xhints", right);
  let busy = false;

  const note = (cls: string, text: string) => {
    status.className = "xstatus " + cls;
    status.textContent = text;
  };
  const text = (cls: string, content: string, parent: HTMLElement = out) => {
    const d = A.el("div", cls, parent);
    d.textContent = content;
    return d;
  };
  const setBusy = (on: boolean) => {
    busy = on;
    runBtn.disabled = checkBtn.disabled = on;
    card.setAttribute("aria-busy", String(on));
  };

  function showHints(n: number) {
    if (!hintBtn) return;
    hints.textContent = "";
    hintList.slice(0, n).forEach((h, k) => {
      const d = A.el("div", "xhint", hints);
      A.el("b", "", d).textContent = `Pista ${k + 1}`;
      A.rich(A.el("div", "", d), h);
    });
    hintBtn.textContent =
      n >= hintList.length
        ? "Sin más pistas"
        : `Pista (${n}/${hintList.length})`;
    hintBtn.disabled = n >= hintList.length;
  }
  function nextHint() {
    const n = Math.min(
      (progress.get(s.exercise).hints || 0) + 1,
      hintList.length,
    );
    progress.set(s.exercise, { hints: n });
    showHints(n);
  }
  if (hintBtn) showHints(Math.min(saved.hints || 0, hintList.length));

  function render(res: RunReply, mode: Mode) {
    const tests = res.tests || [];
    let cls: string, msg: string;
    if (res.error) [cls, msg] = ["bad", "Tu código tiene un error."];
    else if (mode === "run") [cls, msg] = ["ok", "Se ejecutó sin errores."];
    else if (res.passed) [cls, msg] = ["ok", "¡Pasa todos los casos!"];
    else [cls, msg] = ["bad", `Pasan ${tally(tests)}.`];
    note(cls, msg + (res.ms != null ? ` (${seconds(res.ms)})` : ""));
    out.textContent = "";
    if (res.error) {
      text("xerr", res.error);
      const at = /línea (\d+)/.exec(res.error);
      if (at) ed?.markError(+at[1]);
      if (mode === "check")
        text(
          "xlabel",
          "No se pudo probar tu código: corrige el error y vuelve a comprobar.",
        );
    }
    if (res.stdout) {
      text("xlabel", "Salida");
      A.el("pre", "xstdout", out).textContent = res.stdout;
    } else if (mode === "run" && !res.error)
      text("xlabel", "No imprimió nada. Usa print(…) para ver un valor.");
    if (tests.length) {
      const ul = A.el("ul", "xtests", out);
      tests.forEach((t) => {
        const li = A.el("li", t.passed ? "ok" : "bad", ul);
        A.el("span", "xmark", li).textContent = t.passed ? "✓" : "✗";
        const body = A.el("div", "", li);
        A.el("span", "sr", body).textContent = t.passed ? "Pasa: " : "Falla: ";
        A.el("b", "", body).textContent = t.name;
        if (!t.passed && t.message) text("xmsg", t.message, body);
        const tip = hintList[t.hint - 1];
        if (!t.passed && tip) {
          const d = A.el("div", "xhint xcasehint", body);
          A.el("b", "", d).textContent = `Pista ${t.hint}`;
          A.rich(A.el("div", "", d), tip);
        }
      });
    }
    if (mode === "run" && !res.error)
      text("xlabel", "Comprobar prueba tu código con los casos del ejercicio.");
    if (mode === "check") {
      progress.set(s.exercise, {
        checks: (progress.get(s.exercise).checks || 0) + 1,
        ...(res.passed ? { passed: true } : {}),
      });
      if (res.passed) solved.hidden = false;
    }
  }
  const fail = (msg: string) => {
    out.textContent = "";
    note("bad", msg);
  };

  async function send(mode: Mode) {
    if (busy || !ed) return;
    const editor = ed;
    setBusy(true);
    editor.markError(0);
    out.textContent = "";
    note("busy", mode === "check" ? "Comprobando…" : "Ejecutando…");
    const slow = setTimeout(
      () =>
        note(
          "busy",
          "Esperando al corredor. La primera vez puede tardar unos segundos…",
        ),
      SLOW_MS,
    );
    const ctl = new AbortController();
    const cut = setTimeout(() => ctl.abort(), CALL_TIMEOUT_MS);
    try {
      const post = (token?: string) =>
        fetch(RUN_URL, {
          method: "POST",
          signal: ctl.signal,
          headers: {
            "Content-Type": "application/json",
            ...(token && { "X-Turnstile-Token": token }),
          },
          body: JSON.stringify({
            exercise: s.exercise,
            code: editor.get(),
            mode,
          }),
        });
      let resp = await post();
      let body: RunReply | null = await resp.json().catch(() => null);
      if (
        resp.status === 403 &&
        body?.reason === "turnstile_missing" &&
        body.sitekey
      ) {
        note("busy", "Comprobando que eres una persona…");
        resp = await post(
          await turnstileToken(
            body.sitekey,
            A.el("div", "xturnstile", out),
            ctl.signal,
          ),
        );
        body = await resp.json().catch(() => null);
      }
      if (!resp.ok)
        fail(
          HTTP_ERRORS[resp.status] ||
            body?.error ||
            `El corredor respondió ${resp.status}.`,
        );
      else if (typeof body?.passed !== "boolean")
        fail("El corredor respondió algo que no se entiende.");
      else render(body, mode);
    } catch (e) {
      const err = e as Error;
      fail(
        err.name === "AbortError"
          ? `El corredor no respondió en ${CALL_TIMEOUT_MS / 1000} s. Inténtalo de nuevo.`
          : err.message === "turnstile"
            ? "No se pudo cargar la comprobación de que eres una persona. Desactiva el bloqueador de anuncios de esta página e inténtalo de nuevo."
            : "No se pudo conectar con el corredor. Revisa tu conexión e inténtalo de nuevo.",
      );
    } finally {
      clearTimeout(slow);
      clearTimeout(cut);
      setBusy(false);
    }
  }

  setBusy(true);
  loadEditor()
    .catch(() => null)
    .then((lib) => {
      if (!lib) {
        A.el("p", "xerr", host).textContent =
          "No se pudo cargar el editor. Recarga la página.";
        return;
      }
      host.textContent = "";
      ed = lib.create(host, {
        doc: saved.code ?? s.starter,
        label: "Editor de código del ejercicio",
        onChange: (code) => progress.set(s.exercise, { code }),
        onRun: () => send("run"),
        onCheck: () => send("check"),
      });
      setBusy(false);
      note("idle", "Escribe tu código y pulsa Ejecutar o Comprobar.");
    });
  return o;
};
