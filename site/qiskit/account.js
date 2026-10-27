// Cuenta opcional para llevar el progreso a otro navegador (docs/runner.md#cuentas).
// Sin cuenta no hace peticiones de cuenta. Con la marca qiskit:cuenta, junta el
// progreso antes de pintar y envía los cambios que admite el Worker.
// Las reflexiones (qiskit:reflect) no salen del navegador.
/* oxlint-disable unicorn/consistent-function-scoping --
   Script clásico en una función: sus ayudas no pueden salir al ámbito global. */
(() => {
  "use strict";
  const FLAG = "qiskit:cuenta";
  const RETURN_HASH = "#cuenta";
  const SYNC_TIMEOUT_MS = 4000;
  const PUSH_DELAY_MS = 1500;
  const MAX_CODE_BYTES = 20000;

  const LESSON = /^[a-z0-9][a-z0-9-]{0,59}$/;
  const EXERCISE = /^qiskit:exercise:([a-z0-9-]{1,40}\/[a-z0-9-]{1,40})$/;
  const KV =
    /^qiskit:(?:heard:[a-z0-9-]{1,60}|pos:[a-z0-9-]{1,60}|predict:[a-z0-9-]{1,60}:[A-Za-z0-9_-]{1,60}|hitos|misiones|repaso)$/;

  const read = (key) => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  };
  const write = (key, value) => {
    try {
      localStorage.setItem(key, value);
    } catch {}
  };
  const parse = (raw) => {
    try {
      return JSON.parse(raw);
    } catch {
      return undefined;
    }
  };
  const count = (n) => (Number.isSafeInteger(n) && n >= 0 ? n : 0);

  const listeners = new Set();
  const state = { signedIn: read(FLAG) !== null, busy: false, message: "" };
  const update = (patch) => {
    Object.assign(state, patch);
    listeners.forEach((f) => f());
  };
  const forget = () => {
    try {
      localStorage.removeItem(FLAG);
    } catch {}
    update({ signedIn: false });
  };

  function exerciseBody(value) {
    if (typeof value !== "object" || value === null || Array.isArray(value))
      return null;
    const out = {
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

  // Omite valores que harían fallar todo el cuerpo de POST /api/merge.
  function collect(keys) {
    const body = { done: [], exercises: {}, kv: {} };
    for (const key of keys) {
      const value = parse(read(key));
      if (value === undefined) continue;
      const exercise = EXERCISE.exec(key);
      if (key === "qiskit:done") {
        if (Array.isArray(value))
          body.done = value.filter(
            (id) => typeof id === "string" && LESSON.test(id),
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
    const keys = [];
    try {
      for (let k = 0; k < localStorage.length; k++)
        keys.push(localStorage.key(k));
    } catch {}
    return keys;
  };

  // La respuesta incluye lo enviado y reemplaza los valores locales.
  function adopt(progress) {
    const done = new Set([
      ...(parse(read("qiskit:done")) || []),
      ...progress.done,
    ]);
    write("qiskit:done", JSON.stringify([...done]));
    for (const [id, item] of Object.entries(progress.exercises)) {
      const key = `qiskit:exercise:${id}`;
      const local = parse(read(key)) || {};
      write(
        key,
        JSON.stringify({ ...local, ...item, code: item.code ?? local.code }),
      );
    }
    for (const [key, value] of Object.entries(progress.kv))
      write(key, JSON.stringify(value));
  }

  const api = (method, path, body, options = {}) =>
    fetch(path, {
      method,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      ...options,
    });

  // 401: la sesión caducó o se cerró en otro sitio.
  const lapsed = (resp) => {
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
      if (read(FLAG) === null) write(FLAG, "1");
      adopt((await resp.json()).progress);
      update({ signedIn: true, message: "" });
    } catch {
      update({
        message: "No se pudo sincronizar. Tu progreso sigue en este navegador.",
      });
    } finally {
      clearTimeout(cut);
    }
  }

  const dirty = new Set();
  let timer = null,
    pushing = Promise.resolve();
  function flush({ unloading = false } = {}) {
    clearTimeout(timer);
    timer = null;
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
  function changed(key) {
    if (
      !state.signedIn ||
      !(key === "qiskit:done" || EXERCISE.test(key) || KV.test(key))
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

  const signIn = (provider) => {
    const back = location.pathname + location.search + RETURN_HASH;
    location.href = `/auth/${provider}?return=${encodeURIComponent(back)}`;
  };
  async function signOut() {
    flush();
    await pushing;
    try {
      const resp = await api("POST", "/auth/logout");
      if (!resp.ok) throw new Error(String(resp.status));
      forget();
    } catch {
      update({ message: "No se pudo cerrar la sesión. Inténtalo de nuevo." });
    }
  }
  // Borra la cuenta y lo que guarda. La copia de este navegador se queda.
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

  function mount(host) {
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

    const item = (label, onclick, cls = "") => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = cls;
      b.textContent = label;
      b.addEventListener("click", onclick);
      menu.append(b);
    };
    const para = (text) => {
      const p = document.createElement("p");
      p.textContent = text;
      menu.append(p);
    };
    const privacy = () => {
      const a = document.createElement("a");
      a.href = "privacidad.html";
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
            menu.querySelector(".cancel").focus();
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
    // Las teclas del menú no son atajos de la lección.
    host.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !menu.hidden) {
        close();
        button.focus();
      }
      e.stopPropagation();
    });
    // En captura: el clic de un elemento del menú lo repinta, y ya no estaría dentro de `host` al llegar aquí.
    document.addEventListener(
      "click",
      (e) => {
        if (!menu.hidden && !host.contains(e.target)) close();
      },
      true,
    );
    listeners.add(paint);
    paint();
  }
  addEventListener("DOMContentLoaded", () =>
    document.querySelectorAll("[data-account]").forEach(mount),
  );

  // Con la marca, o al volver del proveedor, se junta antes de que la página lea su progreso.
  const returning = location.hash === RETURN_HASH;
  if (returning)
    history.replaceState(null, "", location.pathname + location.search);
  const ready = state.signedIn || returning ? sync() : Promise.resolve();

  window.QGAccount = { ready, changed };
})();
