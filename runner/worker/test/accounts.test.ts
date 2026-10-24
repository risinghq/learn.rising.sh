import { afterEach, describe, expect, it } from "vitest";

import {
  type Harness,
  type Options,
  TOKEN,
  clearOfMinuteEnd,
  start as startWorker,
} from "./harness.ts";
import { PII } from "./provider.ts";
import { begin, cookieOf, setCookies, signIn } from "./signin.ts";

const open: Harness[] = [];

async function worker(options?: Options): Promise<Harness> {
  const h = await startWorker(options);
  open.push(h);
  return h;
}

afterEach(async () => {
  await Promise.all(open.splice(0).map((h) => h.dispose()));
});

const TABLES = [
  "users",
  "identities",
  "sessions",
  "lesson_done",
  "exercise_state",
  "kv",
  "attempts",
];

async function count(h: Harness, table: string, where = "1"): Promise<number> {
  const row = await h.db
    .prepare(`SELECT COUNT(*) AS n FROM ${table} WHERE ${where}`)
    .first<{ n: number }>();
  return row!.n;
}

async function dump(h: Harness): Promise<string> {
  const rows = await Promise.all(
    TABLES.map((table) => h.db.prepare(`SELECT * FROM ${table}`).all()),
  );
  return JSON.stringify(rows.map((r) => r.results));
}

describe("inicio de sesión con OAuth", () => {
  it.each(["google", "github"] as const)(
    "%s manda al alumno con state y PKCE S256",
    async (provider) => {
      const h = await worker();
      const { start, location, flow } = await begin(h, provider);
      expect(start.status).toBe(302);
      const url = new URL(location!);
      expect(url.searchParams.get("response_type")).toBe("code");
      expect(url.searchParams.get("code_challenge_method")).toBe("S256");
      expect(url.searchParams.get("state")).toHaveLength(22);
      expect(url.searchParams.get("redirect_uri")).toBe(
        `http://runner.test/auth/${provider}/callback`,
      );
      // Solo el identificador: ni correo ni nombre.
      expect(url.searchParams.get("scope")).toBe(
        provider === "google" ? "openid" : null,
      );
      const header = setCookies(start.headers).find((line) =>
        line.startsWith("qg_oauth="),
      )!;
      expect(flow).toBeDefined();
      expect(header).toMatch(/HttpOnly/);
      expect(header).toMatch(/Secure/);
      expect(header).toMatch(/SameSite=Lax/);
      expect(header).toMatch(/Path=\/auth/);
    },
  );

  it("rechaza un state que no es el de la salida y no llama al proveedor", async () => {
    const h = await worker();
    const { location, flow } = await begin(h, "google");
    const code = h.provider.consent(location!, "sub-1");
    const back = await h.request(
      "GET",
      `/auth/google/callback?code=${code}&state=otro`,
      {
        headers: { cookie: flow! },
      },
    );
    expect(back.status).toBe(400);
    expect(back.body.reason).toBe("state_mismatch");
    expect(cookieOf(setCookies(back.headers), "qg_auth")).toBeUndefined();
    expect(h.provider.tokenCalls()).toHaveLength(0);
    expect(await count(h, "users")).toBe(0);
  });

  it("rechaza una vuelta sin la cookie de la salida", async () => {
    const h = await worker();
    const { location } = await begin(h, "github");
    const code = h.provider.consent(location!, "7");
    const state = new URL(location!).searchParams.get("state")!;
    const back = await h.request(
      "GET",
      `/auth/github/callback?code=${code}&state=${state}`,
    );
    expect(back.status).toBe(400);
    expect(back.body.reason).toBe("flow_missing");
    expect(h.provider.tokenCalls()).toHaveLength(0);
  });

  it("rechaza el state de un proveedor en la vuelta de otro", async () => {
    const h = await worker();
    const { location, flow } = await begin(h, "google");
    const state = new URL(location!).searchParams.get("state")!;
    const back = await h.request(
      "GET",
      `/auth/github/callback?code=x&state=${state}`,
      {
        headers: { cookie: flow! },
      },
    );
    expect(back.body.reason).toBe("flow_missing");
  });

  it("rechaza un código repetido y no abre otra sesión", async () => {
    const h = await worker();
    const first = await signIn(h, "google", "sub-1");
    expect(first.back.status).toBe(302);
    expect(await count(h, "sessions")).toBe(1);

    // Alguien reenvía la misma vuelta con la misma cookie de salida.
    const replay = await h.request(
      "GET",
      `/auth/google/callback?code=${first.code}&state=${first.state}`,
      { headers: { cookie: first.flow } },
    );
    expect(replay.status).toBe(400);
    expect(replay.body.reason).toBe("code_rejected");
    expect(cookieOf(setCookies(replay.headers), "qg_auth")).toBeUndefined();
    expect(await count(h, "sessions")).toBe(1);
    expect(await count(h, "users")).toBe(1);
  });

  it("rechaza un código repetido también en GitHub, que contesta 200 con error", async () => {
    const h = await worker();
    const first = await signIn(h, "github", "99");
    const replay = await h.request(
      "GET",
      `/auth/github/callback?code=${first.code}&state=${first.state}`,
      { headers: { cookie: first.flow } },
    );
    expect(replay.status).toBe(400);
    expect(replay.body.reason).toBe("code_rejected");
    expect(await count(h, "sessions")).toBe(1);
  });

  it.each([
    "https://evil.example/",
    "//evil.example",
    "/\\evil.example",
    "javascript:alert(1)",
    "evil.example",
    "/\r\nSet-Cookie:x=1",
    `/${"a".repeat(300)}`,
  ])("rechaza el destino %j como redirección abierta", async (target) => {
    const h = await worker();
    const { start } = await begin(
      h,
      "google",
      `?return=${encodeURIComponent(target)}`,
    );
    expect(start.status).toBe(400);
    expect(start.body.reason).toBe("bad_return");
    expect(start.headers.get("location")).toBeNull();
    expect(setCookies(start.headers)).toHaveLength(0);
  });

  it("vuelve solo a la ruta de este sitio que se pidió", async () => {
    const h = await worker();
    const { back } = await signIn(
      h,
      "google",
      "sub-1",
      "?return=/lesson.html%3Fid%3Dqubit%23paso",
    );
    expect(back.status).toBe(302);
    expect(back.headers.get("location")).toBe("/lesson.html?id=qubit#paso");
    const none = await signIn(h, "google", "sub-1", "");
    expect(none.back.headers.get("location")).toBe("/");
  });

  it("vuelve a una ruta con caracteres no ASCII, en porcentaje y sin error", async () => {
    const h = await worker();
    const target = "/lección/€.html?q=ñ";
    const { back } = await signIn(
      h,
      "google",
      "sub-1",
      `?return=${encodeURIComponent(target)}`,
    );
    expect(back.status).toBe(302);
    expect(back.headers.get("location")).toBe(
      "/lecci%C3%B3n/%E2%82%AC.html?q=%C3%B1",
    );
    expect(decodeURI(back.headers.get("location")!)).toBe(target);
  });

  it("no sigue un destino ajeno que venga en una cookie de salida fabricada", async () => {
    const h = await worker();
    const { location } = await begin(h, "google");
    const code = h.provider.consent(location!, "sub-1");
    const state = new URL(location!).searchParams.get("state")!;
    const forged = Buffer.from(
      JSON.stringify({
        provider: "google",
        state,
        verifier: "v".repeat(43),
        next: "//evil.example",
      }),
    ).toString("base64url");
    const back = await h.request(
      "GET",
      `/auth/google/callback?code=${code}&state=${state}`,
      {
        headers: { cookie: `qg_oauth=${forged}` },
      },
    );
    expect(back.status).toBe(400);
    expect(back.body.reason).toBe("flow_missing");
    expect(back.headers.get("location")).toBeNull();
    expect(h.provider.tokenCalls()).toHaveLength(0);
  });

  it("un inicio válido pone qg_auth y crea un solo usuario", async () => {
    const h = await worker();
    const { back, cookie } = await signIn(h, "google", "sub-1");
    expect(back.status).toBe(302);
    expect(back.headers.get("location")).toBe("/lesson.html");
    expect(cookie).toMatch(/^qg_auth=[A-Za-z0-9_-]{43}$/);
    const header = setCookies(back.headers).find((line) =>
      line.startsWith("qg_auth="),
    )!;
    expect(header).toMatch(/HttpOnly/);
    expect(header).toMatch(/Secure/);
    expect(header).toMatch(/SameSite=Lax/);
    expect(header).toMatch(/Path=\//);
    expect(header).toMatch(new RegExp(`Max-Age=${30 * 86400}`));
    expect(
      setCookies(back.headers).find((line) => line.startsWith("qg_oauth=")),
    ).toMatch(/Max-Age=0/);
    expect(await count(h, "users")).toBe(1);
    expect(await count(h, "identities")).toBe(1);

    const me = await h.request("GET", "/api/me", {
      headers: { cookie: cookie! },
    });
    expect(me.body).toMatchObject({ signedIn: true, providers: ["google"] });
  });

  it("el mismo sujeto del proveedor entra en el mismo usuario", async () => {
    const h = await worker();
    const first = await signIn(h, "github", "1234");
    const second = await signIn(h, "github", "1234");
    expect(await count(h, "users")).toBe(1);
    expect(await count(h, "identities")).toBe(1);
    expect(await count(h, "sessions")).toBe(2);
    expect(second.cookie).not.toBe(first.cookie);
    const ids = await h.db
      .prepare("SELECT DISTINCT user_id FROM sessions")
      .all();
    expect(ids.results).toHaveLength(1);
  });

  it("otro sujeto es otro usuario, y el mismo número en otro proveedor también", async () => {
    const h = await worker();
    await signIn(h, "google", "42");
    await signIn(h, "github", "42");
    await signIn(h, "github", "43");
    expect(await count(h, "users")).toBe(3);
    expect(await count(h, "identities")).toBe(3);
  });

  it("de la sesión solo se guarda el hash del token", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    const token = cookie!.slice("qg_auth=".length);
    expect(await dump(h)).not.toContain(token);
    const row = await h.db
      .prepare("SELECT token_hash FROM sessions")
      .first<{ token_hash: string }>();
    const digest = await crypto.subtle.digest(
      "SHA-256",
      new TextEncoder().encode(token),
    );
    expect(row!.token_hash).toBe(Buffer.from(digest).toString("base64url"));
  });

  it("manda el verificador PKCE y el User-Agent que GitHub exige", async () => {
    const h = await worker();
    await signIn(h, "github", "7");
    const [token] = h.provider.tokenCalls();
    expect(token.form.code_verifier).toHaveLength(43);
    expect(token.headers["user-agent"]).toBe("qiskit-guides");
    expect(token.headers.accept).toBe("application/json");
  });

  it("no guarda correo ni nombre aunque el proveedor los devuelva", async () => {
    const h = await worker();
    await signIn(h, "google", "sub-1");
    await signIn(h, "github", "5");
    const all = await dump(h);
    expect(all).not.toContain(PII.email);
    expect(all).not.toContain(PII.name);
    expect(all).not.toContain(PII.login);
  });

  it("si el alumno cancela vuelve a la página sin sesión", async () => {
    const h = await worker();
    const { location, flow } = await begin(h, "google", "?return=/lesson.html");
    const state = new URL(location!).searchParams.get("state")!;
    const back = await h.request(
      "GET",
      `/auth/google/callback?error=access_denied&state=${state}`,
      {
        headers: { cookie: flow! },
      },
    );
    expect(back.status).toBe(302);
    expect(back.headers.get("location")).toBe("/lesson.html");
    expect(cookieOf(setCookies(back.headers), "qg_auth")).toBeUndefined();
    expect(await count(h, "sessions")).toBe(0);
  });

  it("responde 502 si el proveedor no contesta y no crea nada", async () => {
    const h = await worker();
    const { location, flow } = await begin(h, "google");
    const code = h.provider.consent(location!, "sub-1");
    const state = new URL(location!).searchParams.get("state")!;
    h.provider.down.add("google");
    const back = await h.request(
      "GET",
      `/auth/google/callback?code=${code}&state=${state}`,
      {
        headers: { cookie: flow! },
      },
    );
    expect(back.status).toBe(502);
    expect(back.body.reason).toBe("provider_failed");
    expect(await count(h, "users")).toBe(0);
  });

  it("responde 503 si el proveedor no tiene credenciales", async () => {
    const h = await worker({
      vars: { GITHUB_CLIENT_ID: "", GITHUB_CLIENT_SECRET: "" },
    });
    const reply = await h.request("GET", "/auth/github");
    expect(reply.status).toBe(503);
    expect(reply.body.reason).toBe("provider_unavailable");
    expect((await h.request("GET", "/auth/google")).status).toBe(302);
  });

  it("limita los intentos de inicio de sesión por IP", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { AUTH_PER_MINUTE: "3" } });
    const statuses: number[] = [];
    for (let i = 0; i < 4; i++)
      statuses.push((await h.request("GET", "/auth/google")).status);
    expect(statuses).toEqual([302, 302, 302, 429]);
    expect(
      (await h.request("GET", "/auth/google", { ip: "203.0.113.9" })).status,
    ).toBe(302);
  });

  it("responde 404 y 405 a lo que no es una ruta de /auth", async () => {
    const h = await worker();
    expect((await h.request("GET", "/auth/gitlab")).status).toBe(404);
    expect((await h.request("GET", "/auth")).status).toBe(404);
    const wrong = await h.request("POST", "/auth/google");
    expect(wrong.status).toBe(405);
    expect(wrong.headers.get("allow")).toBe("GET");
    expect((await h.request("GET", "/auth/logout")).status).toBe(405);
  });
});

describe("cerrar sesión y caducidad", () => {
  const origin = { origin: "http://runner.test" };

  it("logout borra la sesión y la cookie", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    const out = await h.request("POST", "/auth/logout", {
      headers: { ...origin, cookie: cookie! },
    });
    expect(out.status).toBe(204);
    expect(
      setCookies(out.headers).find((line) => line.startsWith("qg_auth=")),
    ).toMatch(/Max-Age=0/);
    expect(await count(h, "sessions")).toBe(0);
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: cookie! },
    });
    expect(me.body).toEqual({ signedIn: false });
  });

  it("logout exige que la petición venga de este sitio", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    const none = await h.request("POST", "/auth/logout", {
      headers: { cookie: cookie! },
    });
    expect(none.status).toBe(403);
    const foreign = await h.request("POST", "/auth/logout", {
      headers: { origin: "https://evil.example", cookie: cookie! },
    });
    expect(foreign.status).toBe(403);
    expect(await count(h, "sessions")).toBe(1);
  });

  it("una sesión vencida es como no tener sesión", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    await h.db.prepare("UPDATE sessions SET expires_at = 1").run();
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: cookie! },
    });
    expect(me.body).toEqual({ signedIn: false });
    const put = await h.request("PUT", "/api/progress", {
      headers: { ...origin, cookie: cookie! },
      body: { done: ["intro"] },
    });
    expect(put.status).toBe(401);
  });
});

// Quien entró y no mantiene el sitio ejecuta con su cookie y el token de Turnstile.
const signedIn = (cookie: string, extra: Record<string, string> = {}) => ({
  cookie,
  "x-turnstile-token": TOKEN,
  ...extra,
});

describe("/run con cuenta", () => {
  const check = { code: "print(1)", mode: "check", exercise: "intro/uno" };

  it("con sesión pero sin ser mantenedor, Turnstile sigue siendo necesario", async () => {
    const h = await worker({ vars: { MAINTAINERS: "20960328" } });
    const { cookie } = await signIn(h, "github", "4242");
    const without = await h.post(check, { headers: { cookie: cookie! } });
    expect(without.status).toBe(403);
    expect(without.body.reason).toBe("turnstile_missing");
    expect(h.runnerCalls()).toHaveLength(0);

    const verified = await h.post(check, { headers: signedIn(cookie!) });
    expect(verified.status).toBe(200);
    expect(h.siteverify.calls).toHaveLength(1);
  });

  it("un mantenedor de GitHub ejecuta sin Turnstile ni límite por usuario", async () => {
    await clearOfMinuteEnd();
    const h = await worker({
      vars: {
        MAINTAINERS: "7,20960328",
        RATE_PER_MINUTE: "2",
        SIGNED_IN_IP_FACTOR: "100",
      },
    });
    const { cookie } = await signIn(h, "github", "20960328");
    const statuses: number[] = [];
    for (let i = 0; i < 4; i++)
      statuses.push(
        (await h.post(check, { headers: { cookie: cookie! } })).status,
      );
    expect(statuses).toEqual([200, 200, 200, 200]);
    expect(h.siteverify.calls).toHaveLength(0);
    expect(await count(h, "attempts", "user_id IS NOT NULL")).toBe(4);
  });

  it("el mismo número en Google no hace mantenedor, y el límite por usuario sí le llega", async () => {
    await clearOfMinuteEnd();
    const h = await worker({
      vars: {
        MAINTAINERS: "20960328",
        RATE_PER_MINUTE: "2",
        SIGNED_IN_IP_FACTOR: "100",
      },
    });
    // El primer intento, sin token, ya cuenta en el límite del usuario.
    const { cookie } = await signIn(h, "google", "20960328");
    const reply = await h.post(check, { headers: { cookie: cookie! } });
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_missing");
    const statuses = [];
    for (let i = 0; i < 2; i++)
      statuses.push(
        (await h.post(check, { headers: signedIn(cookie!) })).status,
      );
    expect(statuses).toEqual([200, 429]);
  });

  it("MAINTAINERS con un nombre de usuario en vez de un id es un error de configuración", async () => {
    const h = await worker({ vars: { MAINTAINERS: "totallynotdavid" } });
    const reply = await h.post(check, { headers: signedIn("qg_auth=x") });
    expect(reply.status).toBe(500);
    expect(h.workerLogs().join("\n")).toContain("MAINTAINERS");
  });

  it("sin sesión y sin token sigue respondiendo 403", async () => {
    const h = await worker();
    const reply = await h.post(check);
    expect(reply.status).toBe(403);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("una cookie qg_auth inventada no salta Turnstile", async () => {
    const h = await worker();
    const reply = await h.post(check, {
      headers: { cookie: "qg_auth=inventada" },
    });
    expect(reply.status).toBe(403);
  });

  it("cada usuario tiene su propio límite por minuto", async () => {
    await clearOfMinuteEnd();
    const h = await worker({
      vars: { RATE_PER_MINUTE: "2", SIGNED_IN_IP_FACTOR: "100" },
    });
    const ada = await signIn(h, "google", "ada");
    const bea = await signIn(h, "google", "bea");
    const statuses = async (cookie: string) => {
      const out: number[] = [];
      for (let i = 0; i < 3; i++)
        out.push((await h.post(check, { headers: signedIn(cookie) })).status);
      return out;
    };
    expect(await statuses(ada.cookie!)).toEqual([200, 200, 429]);
    expect(await statuses(bea.cookie!)).toEqual([200, 200, 429]);
  });

  it("con cuenta la IP admite cuatro veces el tope anónimo", async () => {
    await clearOfMinuteEnd();
    // Cada usuario tiene su cuenta (3) y la IP compartida solo 2 × 4.
    const h = await worker({
      vars: { RATE_PER_MINUTE: "2", SIGNED_IN_IP_FACTOR: "4" },
    });
    const users = await Promise.all(
      ["a", "b", "c", "d", "e"].map((subject) => signIn(h, "google", subject)),
    );
    const statuses: number[] = [];
    for (const user of users) {
      for (let i = 0; i < 2; i++)
        statuses.push(
          (await h.post(check, { headers: signedIn(user.cookie!) })).status,
        );
    }
    // Ocho ejecuciones caben; la novena de la misma IP ya no.
    expect(statuses.slice(0, 8)).toEqual(Array(8).fill(200));
    expect(statuses.slice(8)).toEqual([429, 429]);
  });

  it("la IP anónima conserva su tope sin multiplicar", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "2" } });
    const headers = { "x-turnstile-token": TOKEN };
    const statuses: number[] = [];
    for (let i = 0; i < 3; i++)
      statuses.push((await h.post(check, { headers })).status);
    expect(statuses).toEqual([200, 200, 429]);
  });
});

describe("intentos", () => {
  const MARKER = "MARCA-SECRETA-7731";

  async function attempts(h: Harness) {
    const rows = await h.db
      .prepare("SELECT * FROM attempts ORDER BY id")
      .all<Record<string, any>>();
    return rows.results;
  }

  it("tras un check que falla guarda los casos fallidos y nada del código ni del texto", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    const code = `# FALLA ${MARKER}\nprint('${MARKER}')`;
    const reply = await h.post(
      { code, mode: "check", exercise: "intro/uno" },
      { headers: signedIn(cookie!, { "x-hints": "2" }) },
    );
    expect(reply.status).toBe(200);
    // El corredor sí repite el marcador en lo que le devuelve a la página.
    expect(JSON.stringify(reply.body)).toContain(MARKER);

    const [row, ...rest] = await attempts(h);
    expect(rest).toHaveLength(0);
    expect(row).toMatchObject({
      mode: "check",
      exercise: "intro/uno",
      outcome: "fail",
      hints: 2,
      ms: 42,
      code_bytes: new TextEncoder().encode(code).length,
      error_kind: null,
    });
    expect(row.user_id).toMatch(/^[A-Za-z0-9_-]{22}$/);
    expect(JSON.parse(row.failed)).toEqual(["n = 2, 3 y 4", "caso oculto 1"]);
    // Ninguna columna de ninguna tabla lleva el marcador.
    expect(await dump(h)).not.toContain(MARKER);
    expect(await dump(h)).not.toContain("salió");
  });

  it("un error de Python guarda solo el nombre de la excepción", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    await h.post(
      { code: `ERROR ${MARKER}`, mode: "run", exercise: "intro/uno" },
      { headers: signedIn(cookie!) },
    );
    const [row] = await attempts(h);
    expect(row).toMatchObject({
      outcome: "error",
      error_kind: "NameError",
      mode: "run",
    });
    expect(await dump(h)).not.toContain(MARKER);
    expect(await dump(h)).not.toContain("is not defined");
  });

  it("un texto de error que no es una excepción se guarda como «other»", async () => {
    const h = await worker();
    await h.post(
      { code: `ERROR-RARO ${MARKER}`, mode: "run", exercise: "intro/uno" },
      { headers: { "x-turnstile-token": TOKEN } },
    );
    const [row] = await attempts(h);
    expect(row).toMatchObject({ outcome: "error", error_kind: "other" });
    expect(await dump(h)).not.toContain(MARKER);
  });

  it("un corte por tiempo es «timeout» y un acierto es «pass»", async () => {
    const h = await worker();
    const headers = { "x-turnstile-token": TOKEN };
    await h.post(
      { code: `MATADO ${MARKER}`, mode: "check", exercise: "intro/uno" },
      { headers },
    );
    await h.post(
      { code: "print(1)", mode: "check", exercise: "intro/uno" },
      { headers },
    );
    const rows = await attempts(h);
    expect(rows.map((r) => r.outcome)).toEqual(["timeout", "pass"]);
    expect(JSON.parse(rows[1].failed)).toEqual([]);
    expect(await dump(h)).not.toContain(MARKER);
  });

  it("una ejecución anónima escribe una fila con user_id NULL", async () => {
    const h = await worker();
    const reply = await h.post(
      { code: "print(1)", mode: "run", exercise: "intro/uno" },
      { headers: { "x-turnstile-token": TOKEN } },
    );
    expect(reply.status).toBe(200);
    const [row, ...rest] = await attempts(h);
    expect(rest).toHaveLength(0);
    expect(row.user_id).toBeNull();
    expect(row.outcome).toBe("pass");
    expect(await count(h, "users")).toBe(0);
  });

  it("no anota sin ejercicio válido, con un modo desconocido ni con una cabecera de pistas rara", async () => {
    const h = await worker();
    const headers = { "x-turnstile-token": TOKEN };
    await h.post({ code: "print(1)", mode: "run" }, { headers });
    await h.post(
      { code: "print(1)", mode: "run", exercise: "../etc/passwd" },
      { headers },
    );
    await h.post(
      { code: "print(1)", mode: "otro", exercise: "intro/uno" },
      { headers },
    );
    expect(await attempts(h)).toHaveLength(0);
    await h.post(
      { code: "print(1)", mode: "run", exercise: "intro/uno" },
      { headers: { ...headers, "x-hints": "mucho" } },
    );
    expect((await attempts(h))[0].hints).toBe(0);
  });

  it("una petición rechazada no deja fila", async () => {
    const h = await worker();
    const run = { code: "print(1)", mode: "run", exercise: "intro/uno" };
    expect((await h.post(run)).status).toBe(403);
    expect(
      (
        await h.post(
          { ...run, code: "x".repeat(30_000) },
          { headers: { "x-turnstile-token": TOKEN } },
        )
      ).status,
    ).toBe(413);
    expect(await attempts(h)).toHaveLength(0);
  });

  it("si la base falla, la página recibe igualmente el resultado", async () => {
    const h = await worker();
    await h.db.prepare("DROP TABLE attempts").run();
    const reply = await h.post(
      { code: "print(1)", mode: "run", exercise: "intro/uno" },
      { headers: { "x-turnstile-token": TOKEN } },
    );
    expect(reply.status).toBe(200);
    expect(reply.body.passed).toBe(true);
    expect(h.workerLogs().join("\n")).toContain("attempt");
  });
});

describe("/api", () => {
  const origin = { origin: "http://runner.test" };

  async function user(h: Harness, subject = "sub-1") {
    const { cookie } = await signIn(h, "google", subject);
    return { cookie: cookie! };
  }
  const put = (
    h: Harness,
    cookie: string,
    body: unknown,
    path = "/api/progress",
  ) =>
    h.request(path === "/api/merge" ? "POST" : "PUT", path, {
      headers: { ...origin, cookie },
      body,
    });

  it("sin sesión /api/me dice que nadie entró y lo demás responde 401", async () => {
    const h = await worker();
    expect((await h.request("GET", "/api/me")).body).toEqual({
      signedIn: false,
    });
    expect(
      (await h.request("POST", "/api/merge", { headers: origin, body: {} }))
        .status,
    ).toBe(401);
    expect(
      (await h.request("PUT", "/api/progress", { headers: origin, body: {} }))
        .status,
    ).toBe(401);
    expect(
      (await h.request("DELETE", "/api/me", { headers: origin })).status,
    ).toBe(401);
  });

  it("rechaza el origen ajeno, el contenido que no es JSON y los métodos erróneos", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    const foreign = await h.request("PUT", "/api/progress", {
      headers: { origin: "https://evil.example", cookie },
      body: { done: [] },
    });
    expect(foreign.status).toBe(403);
    const noOrigin = await h.request("DELETE", "/api/me", {
      headers: { cookie },
    });
    expect(noOrigin.status).toBe(403);
    expect(await count(h, "users")).toBe(1);

    const text = await h.request("PUT", "/api/progress", {
      headers: { ...origin, cookie, "content-type": "text/plain" },
      body: { done: [] },
    });
    expect(text.status).toBe(415);
    const wrong = await h.request("GET", "/api/progress", {
      headers: { cookie },
    });
    expect(wrong.status).toBe(405);
    expect(wrong.headers.get("allow")).toBe("PUT");
    expect((await h.request("GET", "/api/nada")).status).toBe(404);
  });

  it.each([
    ["una lista que no es", { done: "intro" }],
    ["un id de lección con ruta", { done: ["../x"] }],
    ["un campo desconocido", { otro: 1 }],
    ["un ejercicio mal formado", { exercises: { "intro/uno": { hints: -1 } } }],
    [
      "un id de ejercicio inválido",
      {
        exercises: {
          "Intro/UNO": { hints: 0, checks: 0, passed: false, at: 1 },
        },
      },
    ],
    ["una clave de kv desconocida", { kv: { "qiskit:otra": [1] } }],
    ["un valor de kv de otra forma", { kv: { "qiskit:hitos": "uno" } }],
    [
      "un código enorme",
      {
        exercises: {
          "intro/uno": {
            code: "x".repeat(20_001),
            hints: 0,
            checks: 0,
            passed: false,
            at: 1,
          },
        },
      },
    ],
    ["un arreglo en la raíz", [1, 2]],
  ])("responde 400 a %s", async (_label, body) => {
    const h = await worker();
    const { cookie } = await user(h);
    const reply = await put(h, cookie, body);
    expect(reply.status).toBe(400);
    expect(await count(h, "lesson_done")).toBe(0);
    expect(await count(h, "exercise_state")).toBe(0);
    expect(await count(h, "kv")).toBe(0);
  });

  it("responde 400 a un JSON roto", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    const broken = await h.request("PUT", "/api/progress", {
      headers: { ...origin, cookie, "content-type": "application/json" },
    });
    expect(broken.status).toBe(400);
  });

  it("rechaza un cuerpo enorme sin guardar nada", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    // Solo el encabezado: el 413 llega sin que el cuerpo se haya enviado.
    const status = await h.declare("PUT", "/api/progress", 900_001, {
      ...origin,
      cookie,
      "content-type": "application/json",
    });
    expect(status).toBe(413);
    expect(await count(h, "kv")).toBe(0);
  });

  it("varias escrituras a la vez del mismo usuario no se pisan", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    const lessons = ["a", "b", "c", "d", "e"];
    const replies = await Promise.all(
      lessons.map((lesson, i) =>
        put(h, cookie, {
          done: [lesson],
          exercises: {
            [`intro/e${i}`]: {
              code: `c${i}`,
              hints: i,
              checks: 1,
              passed: false,
              at: 10 + i,
            },
          },
          kv: { "qiskit:hitos": [i] },
        }),
      ),
    );
    expect(replies.map((r) => r.status)).toEqual(lessons.map(() => 204));
    const me = (await h.request("GET", "/api/me", { headers: { cookie } })).body
      .progress;
    expect(me.done).toEqual(lessons);
    expect(Object.keys(me.exercises).toSorted()).toEqual(
      lessons.map((_, i) => `intro/e${i}`),
    );
    expect(me.kv["qiskit:hitos"]).toEqual([0, 1, 2, 3, 4]);
  });

  it("merge une el progreso local con el de la cuenta y devuelve el resultado", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    await put(h, cookie, {
      done: ["intro", "qubit"],
      exercises: {
        "intro/uno": {
          code: "viejo",
          hints: 1,
          checks: 3,
          passed: false,
          at: 1000,
        },
      },
      kv: {
        "qiskit:hitos": [1, 3],
        "qiskit:pos:intro": 4,
        "qiskit:predict:intro:p1": 2,
        "qiskit:repaso": { a: { box: 2, due: 50 }, b: { box: 1, due: 10 } },
      },
    });
    const merged = await put(
      h,
      cookie,
      {
        done: ["qubit", "puertas"],
        exercises: {
          "intro/uno": {
            code: "nuevo",
            hints: 0,
            checks: 5,
            passed: true,
            at: 2000,
          },
          "intro/dos": { hints: 2, checks: 1, passed: false, at: 500 },
        },
        kv: {
          "qiskit:hitos": [2, 3],
          "qiskit:pos:intro": 2,
          "qiskit:predict:intro:p1": 9,
          "qiskit:repaso": {
            a: { box: 3, due: 90 },
            b: { box: 1, due: 5 },
            c: { box: 0, due: 1 },
          },
        },
      },
      "/api/merge",
    );
    expect(merged.status).toBe(200);
    expect(merged.body.progress).toEqual({
      done: ["intro", "puertas", "qubit"],
      exercises: {
        // Gana el código más reciente; pistas y comprobaciones, el máximo; pasar no se pierde.
        "intro/uno": {
          code: "nuevo",
          hints: 1,
          checks: 5,
          passed: true,
          at: 2000,
        },
        "intro/dos": { hints: 2, checks: 1, passed: false, at: 500 },
      },
      kv: {
        "qiskit:hitos": [1, 2, 3],
        "qiskit:pos:intro": 4,
        // La primera apuesta es la que vale.
        "qiskit:predict:intro:p1": 2,
        "qiskit:repaso": {
          a: { box: 3, due: 90 },
          b: { box: 1, due: 5 },
          c: { box: 0, due: 1 },
        },
      },
    });
    const me = await h.request("GET", "/api/me", { headers: { cookie } });
    expect(me.body.progress).toEqual(merged.body.progress);
  });

  it("un código viejo no pisa al nuevo y un null no borra el guardado", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    await put(h, cookie, {
      exercises: {
        "intro/uno": {
          code: "reciente",
          hints: 0,
          checks: 0,
          passed: false,
          at: 2000,
        },
      },
    });
    await put(h, cookie, {
      exercises: {
        "intro/uno": {
          code: "antiguo",
          hints: 0,
          checks: 0,
          passed: false,
          at: 1000,
        },
      },
    });
    await put(h, cookie, {
      exercises: {
        "intro/uno": {
          code: null,
          hints: 0,
          checks: 0,
          passed: false,
          at: 3000,
        },
      },
    });
    const me = await h.request("GET", "/api/me", { headers: { cookie } });
    expect(me.body.progress.exercises["intro/uno"].code).toBe("reciente");
  });

  it("dos sesiones de la misma cuenta acaban con el mismo estado sea cual sea el orden", async () => {
    const h = await worker();
    const first = await user(h);
    const second = await signIn(h, "google", "sub-1");
    const a = {
      done: ["intro"],
      kv: { "qiskit:hitos": [1], "qiskit:pos:intro": 3 },
    };
    const b = {
      done: ["qubit"],
      kv: { "qiskit:hitos": [2], "qiskit:pos:intro": 7 },
    };
    await put(h, first.cookie, a);
    await put(h, second.cookie!, b);
    const one = await h.request("GET", "/api/me", {
      headers: { cookie: first.cookie },
    });

    const other = await worker();
    const x = await user(other);
    const y = await signIn(other, "google", "sub-1");
    await put(other, y.cookie!, b);
    await put(other, x.cookie, a);
    const two = await other.request("GET", "/api/me", {
      headers: { cookie: x.cookie },
    });
    expect(one.body.progress).toEqual(two.body.progress);
    expect(one.body.progress.kv["qiskit:hitos"]).toEqual([1, 2]);
  });

  it("el progreso de un usuario no se ve desde otro", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await put(h, ada.cookie, { done: ["intro"] });
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: bea.cookie },
    });
    expect(me.body.progress.done).toEqual([]);
  });

  it("DELETE /api/me no deja ninguna fila del usuario en ninguna tabla", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await signIn(h, "github", "77"); // otra sesión y otra identidad ajenas
    for (const who of [ada, bea]) {
      await put(h, who.cookie, {
        done: ["intro"],
        exercises: {
          "intro/uno": { code: "a", hints: 0, checks: 1, passed: true, at: 10 },
        },
        kv: { "qiskit:hitos": [1] },
      });
      await h.post(
        { code: "FALLA", mode: "check", exercise: "intro/uno" },
        { headers: signedIn(who.cookie) },
      );
    }
    await h.post(
      { code: "print(1)", mode: "run", exercise: "intro/uno" },
      { headers: { "x-turnstile-token": TOKEN } },
    );
    // Una segunda sesión de Ada, para probar que también cae.
    await signIn(h, "google", "ada");

    const adaId = (await h.db
      .prepare(
        "SELECT user_id FROM identities WHERE provider = 'google' AND subject = 'ada'",
      )
      .first<{ user_id: string }>())!.user_id;
    for (const table of TABLES) {
      if (table === "users") continue;
      // Todas las tablas tienen filas de Ada antes de borrar.
      expect(
        await count(h, table, `user_id = '${adaId}'`),
        table,
      ).toBeGreaterThan(0);
    }

    const out = await h.request("DELETE", "/api/me", {
      headers: { ...origin, cookie: ada.cookie },
    });
    expect(out.status).toBe(200);
    expect(out.body).toEqual({ deleted: true });
    expect(
      setCookies(out.headers).find((line) => line.startsWith("qg_auth=")),
    ).toMatch(/Max-Age=0/);

    expect(await count(h, "users", `id = '${adaId}'`)).toBe(0);
    for (const table of TABLES) {
      if (table === "users") continue;
      expect(await count(h, table, `user_id = '${adaId}'`), table).toBe(0);
    }
    // Lo de los demás sigue: Bea, el usuario de GitHub y el intento anónimo.
    expect(await count(h, "users")).toBe(2);
    expect(await count(h, "lesson_done")).toBe(1);
    expect(await count(h, "attempts", "user_id IS NULL")).toBe(1);
    expect(await count(h, "attempts")).toBe(2);
    // La cookie vieja ya no vale.
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: ada.cookie },
    });
    expect(me.body).toEqual({ signedIn: false });
  });
});

describe("limpieza diaria", () => {
  const DAY = 86_400;

  async function insertAttempt(
    h: Harness,
    at: number,
    userId: string | null = null,
  ) {
    await h.db
      .prepare(
        `INSERT INTO attempts (at, user_id, exercise, mode, outcome, ms, code_bytes)
         VALUES (?1, ?2, 'intro/uno', 'run', 'pass', 1, 1)`,
      )
      .bind(at, userId)
      .run();
  }

  it("borra un intento de más de 180 días y deja el reciente", async () => {
    const h = await worker();
    const now = Math.floor(Date.now() / 1000);
    await insertAttempt(h, now - 181 * DAY);
    await insertAttempt(h, now - 179 * DAY);
    expect(await count(h, "attempts")).toBe(2);
    await h.purge();
    const left = await h.db
      .prepare("SELECT at FROM attempts")
      .all<{ at: number }>();
    expect(left.results.map((r) => r.at)).toEqual([now - 179 * DAY]);
  });

  it("borra las cuentas sin visitas en 24 meses con todo lo suyo, y las sesiones vencidas", async () => {
    const h = await worker();
    const old = await signIn(h, "google", "vieja");
    const live = await signIn(h, "google", "activa");
    const today = Math.floor(Date.now() / 86_400_000);
    await h.post(
      { code: "print(1)", mode: "run", exercise: "intro/uno" },
      { headers: signedIn(old.cookie!) },
    );
    await h.db
      .prepare(
        "UPDATE users SET seen_day = ?1 WHERE id = (SELECT user_id FROM identities WHERE subject = 'vieja')",
      )
      .bind(today - 731)
      .run();
    await h.request("PUT", "/api/progress", {
      headers: { origin: "http://runner.test", cookie: live.cookie! },
      body: { done: ["intro"] },
    });
    await h.db
      .prepare(
        "INSERT INTO sessions (token_hash, user_id, expires_at) SELECT 'vencida', user_id, 1 FROM identities WHERE subject = 'activa'",
      )
      .run();

    await h.purge();
    expect(await count(h, "users")).toBe(1);
    expect(await count(h, "identities", "subject = 'vieja'")).toBe(0);
    expect(await count(h, "sessions")).toBe(1);
    expect(await count(h, "attempts")).toBe(0);
    expect(await count(h, "lesson_done")).toBe(1);
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: live.cookie! },
    });
    expect(me.body.signedIn).toBe(true);
  });

  it("usa los plazos que fija el entorno", async () => {
    const h = await worker({ vars: { ATTEMPT_RETENTION_DAYS: "10" } });
    const now = Math.floor(Date.now() / 1000);
    await insertAttempt(h, now - 11 * DAY);
    await insertAttempt(h, now - 9 * DAY);
    await h.purge();
    expect(await count(h, "attempts")).toBe(1);
  });
});
