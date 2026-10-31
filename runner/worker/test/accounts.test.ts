import { afterEach, describe, expect, it } from "vitest";

import {
  type Harness,
  HOME_HOST,
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

describe("OAuth sign-in", () => {
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
      // The return URI comes from the request host, so the site's domain
      // carries it with no further configuration.
      const home = await h.request("GET", `/auth/${provider}`, {
        host: HOME_HOST,
      });
      expect(
        new URL(home.headers.get("location")!).searchParams.get("redirect_uri"),
      ).toBe(`http://${HOME_HOST}/auth/${provider}/callback`);
      // Only the identifier: no email, no name.
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

  it("rejects a state that is not the one from the redirect out and does not call the provider", async () => {
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

  it("rejects a return without the cookie from the redirect out", async () => {
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

  it("rejects the state of one provider on the return of another", async () => {
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

  it("rejects a repeated code and does not open another session", async () => {
    const h = await worker();
    const first = await signIn(h, "google", "sub-1");
    expect(first.back.status).toBe(302);
    expect(await count(h, "sessions")).toBe(1);

    // Someone replays the same return with the same outbound cookie.
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

  it("rejects a repeated code on GitHub too, which answers 200 with an error", async () => {
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
  ])("rejects the target %j as an open redirect", async (target) => {
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

  it("returns only to the path of this site that was requested", async () => {
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

  it("returns to a path with non-ASCII characters, percent-encoded and without error", async () => {
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

  it("does not follow a foreign target that comes in a forged outbound cookie", async () => {
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

  it("a valid sign-in sets qg_auth and creates a single user", async () => {
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

  it("the same provider subject signs in as the same user", async () => {
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

  it("another subject is another user, and so is the same number on another provider", async () => {
    const h = await worker();
    await signIn(h, "google", "42");
    await signIn(h, "github", "42");
    await signIn(h, "github", "43");
    expect(await count(h, "users")).toBe(3);
    expect(await count(h, "identities")).toBe(3);
  });

  it("only the hash of the token is stored for the session", async () => {
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

  it("sends the PKCE verifier and the User-Agent that GitHub requires", async () => {
    const h = await worker();
    await signIn(h, "github", "7");
    const [token] = h.provider.tokenCalls();
    expect(token.form.code_verifier).toHaveLength(43);
    expect(token.headers["user-agent"]).toBe("qiskit-guides");
    expect(token.headers.accept).toBe("application/json");
  });

  it("stores no email or name even if the provider returns them", async () => {
    const h = await worker();
    await signIn(h, "google", "sub-1");
    await signIn(h, "github", "5");
    const all = await dump(h);
    expect(all).not.toContain(PII.email);
    expect(all).not.toContain(PII.name);
    expect(all).not.toContain(PII.login);
  });

  it("if the learner cancels, they return to the page without a session", async () => {
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

  it("answers 502 if the provider does not reply and creates nothing", async () => {
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

  it("answers 503 if the provider has no credentials", async () => {
    const h = await worker({
      vars: { GITHUB_CLIENT_ID: "", GITHUB_CLIENT_SECRET: "" },
    });
    const reply = await h.request("GET", "/auth/github");
    expect(reply.status).toBe(503);
    expect(reply.body.reason).toBe("provider_unavailable");
    expect((await h.request("GET", "/auth/google")).status).toBe(302);
  });

  it("limits sign-in attempts per IP", async () => {
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

  it("answers 404 and 405 to what is not an /auth route", async () => {
    const h = await worker();
    expect((await h.request("GET", "/auth/gitlab")).status).toBe(404);
    expect((await h.request("GET", "/auth")).status).toBe(404);
    const wrong = await h.request("POST", "/auth/google");
    expect(wrong.status).toBe(405);
    expect(wrong.headers.get("allow")).toBe("GET");
    expect((await h.request("GET", "/auth/logout")).status).toBe(405);
  });
});

describe("sign-out and expiry", () => {
  const origin = { origin: "http://runner.test" };

  it("logout deletes the session and the cookie", async () => {
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

  it("logout requires the request to come from this site", async () => {
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

  it("an expired session is the same as no session", async () => {
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

// A signed-in user who does not maintain the site runs with their cookie and the Turnstile token.
const signedIn = (cookie: string, extra: Record<string, string> = {}) => ({
  cookie,
  "x-turnstile-token": TOKEN,
  ...extra,
});

describe("/run with an account", () => {
  const check = { code: "print(1)", mode: "check", exercise: "intro/uno" };

  it("with a session but not a maintainer, Turnstile is still required", async () => {
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

  it("a GitHub maintainer runs without Turnstile or a per-user limit", async () => {
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

  it("the same number on Google does not make a maintainer, and the per-user limit does apply", async () => {
    await clearOfMinuteEnd();
    const h = await worker({
      vars: {
        MAINTAINERS: "20960328",
        RATE_PER_MINUTE: "2",
        SIGNED_IN_IP_FACTOR: "100",
      },
    });
    // The first attempt, without a token, already counts toward the user's limit.
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

  it("MAINTAINERS with a username instead of an id is a configuration error", async () => {
    const h = await worker({ vars: { MAINTAINERS: "totallynotdavid" } });
    const reply = await h.post(check, { headers: signedIn("qg_auth=x") });
    expect(reply.status).toBe(500);
    expect(h.workerLogs().join("\n")).toContain("MAINTAINERS");
  });

  it("without a session and without a token it still answers 403", async () => {
    const h = await worker();
    const reply = await h.post(check);
    expect(reply.status).toBe(403);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("a made-up qg_auth cookie does not skip Turnstile", async () => {
    const h = await worker();
    const reply = await h.post(check, {
      headers: { cookie: "qg_auth=inventada" },
    });
    expect(reply.status).toBe(403);
  });

  it("each user has their own per-minute limit", async () => {
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

  it("with an account the IP allows four times the anonymous cap", async () => {
    await clearOfMinuteEnd();
    // Each user has their own allowance (3) and the shared IP only 2 × 4.
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
    // Eight runs fit; the ninth from the same IP does not.
    expect(statuses.slice(0, 8)).toEqual(Array(8).fill(200));
    expect(statuses.slice(8)).toEqual([429, 429]);
  });

  it("the anonymous IP keeps its cap without multiplying", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "2" } });
    const headers = { "x-turnstile-token": TOKEN };
    const statuses: number[] = [];
    for (let i = 0; i < 3; i++)
      statuses.push((await h.post(check, { headers })).status);
    expect(statuses).toEqual([200, 200, 429]);
  });
});

describe("attempts", () => {
  const MARKER = "MARCA-SECRETA-7731";

  async function attempts(h: Harness) {
    const rows = await h.db
      .prepare("SELECT * FROM attempts ORDER BY id")
      .all<Record<string, any>>();
    return rows.results;
  }

  it("after a failing check it stores the failed cases and nothing of the code or the text", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    const code = `# FALLA ${MARKER}\nprint('${MARKER}')`;
    const reply = await h.post(
      { code, mode: "check", exercise: "intro/uno" },
      { headers: signedIn(cookie!, { "x-hints": "2" }) },
    );
    expect(reply.status).toBe(200);
    // The runner does repeat the marker in what it returns to the page.
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
    // No column of any table carries the marker.
    expect(await dump(h)).not.toContain(MARKER);
    expect(await dump(h)).not.toContain("salió");
  });

  it("a Python error stores only the exception name", async () => {
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

  it('an error text that is not an exception is stored as "other"', async () => {
    const h = await worker();
    await h.post(
      { code: `ERROR-RARO ${MARKER}`, mode: "run", exercise: "intro/uno" },
      { headers: { "x-turnstile-token": TOKEN } },
    );
    const [row] = await attempts(h);
    expect(row).toMatchObject({ outcome: "error", error_kind: "other" });
    expect(await dump(h)).not.toContain(MARKER);
  });

  it('a cut-off by time is "timeout" and a success is "pass"', async () => {
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

  it("an anonymous run writes a row with user_id NULL", async () => {
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

  it("records nothing without a valid exercise, with an unknown mode or with an odd hints header", async () => {
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

  it("a rejected request leaves no row", async () => {
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

  it("if the database fails, the page still receives the result", async () => {
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

  it("without a session /api/me says nobody signed in and the rest answers 401", async () => {
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

  it("rejects a foreign origin, non-JSON content and wrong methods", async () => {
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
    ["a non-list where a list belongs", { done: "intro" }],
    ["a lesson id with a path", { done: ["../x"] }],
    ["an unknown field", { otro: 1 }],
    ["a malformed exercise", { exercises: { "intro/uno": { hints: -1 } } }],
    [
      "an invalid exercise id",
      {
        exercises: {
          "Intro/UNO": { hints: 0, checks: 0, passed: false, at: 1 },
        },
      },
    ],
    ["an unknown kv key", { kv: { "qiskit:otra": [1] } }],
    ["a kv value of another shape", { kv: { "qiskit:hitos": "uno" } }],
    [
      "a huge code",
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
    ["an array at the root", [1, 2]],
  ])("answers 400 to %s", async (_label, body) => {
    const h = await worker();
    const { cookie } = await user(h);
    const reply = await put(h, cookie, body);
    expect(reply.status).toBe(400);
    expect(await count(h, "lesson_done")).toBe(0);
    expect(await count(h, "exercise_state")).toBe(0);
    expect(await count(h, "kv")).toBe(0);
  });

  it("answers 400 to broken JSON", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    const broken = await h.request("PUT", "/api/progress", {
      headers: { ...origin, cookie, "content-type": "application/json" },
    });
    expect(broken.status).toBe(400);
  });

  it("rejects a huge body without storing anything", async () => {
    const h = await worker();
    const { cookie } = await user(h);
    // Only the header: the 413 arrives without the body having been sent.
    const status = await h.declare("PUT", "/api/progress", 900_001, {
      ...origin,
      cookie,
      "content-type": "application/json",
    });
    expect(status).toBe(413);
    expect(await count(h, "kv")).toBe(0);
  });

  it("several simultaneous writes of the same user do not overwrite each other", async () => {
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

  it("merge joins the local progress with the account's and returns the result", async () => {
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
        "qiskit:repaso": [
          { item: "a", at: 50, correct: true },
          { item: "b", at: 10, correct: true },
        ],
        "computational-physics:hitos": [1],
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
          "qiskit:repaso": [
            { item: "a", at: 90, correct: true },
            { item: "b", at: 10, correct: false },
            { item: "c", at: 1, correct: true },
          ],
          "computational-physics:hitos": [2],
        },
      },
      "/api/merge",
    );
    expect(merged.status).toBe(200);
    expect(merged.body.progress).toEqual({
      done: ["intro", "puertas", "qubit"],
      exercises: {
        // The most recent code wins. Hints and checks take the maximum. The claimed pass is ignored.
        "intro/uno": {
          code: "nuevo",
          hints: 1,
          checks: 5,
          passed: false,
          at: 2000,
        },
        "intro/dos": { hints: 2, checks: 1, passed: false, at: 500 },
      },
      kv: {
        "qiskit:hitos": [1, 2, 3],
        "qiskit:pos:intro": 4,
        // The first bet is the one that counts.
        "qiskit:predict:intro:p1": 2,
        // Both logs are kept, oldest first. A miss and a right answer at the same moment count as a miss.
        "qiskit:repaso": [
          { item: "c", at: 1, correct: true },
          { item: "b", at: 10, correct: false },
          { item: "a", at: 50, correct: true },
          { item: "a", at: 90, correct: true },
        ],
        "computational-physics:hitos": [1, 2],
      },
    });
    const me = await h.request("GET", "/api/me", { headers: { cookie } });
    expect(me.body.progress).toEqual(merged.body.progress);
  });

  it("an old code does not overwrite the new one and a null does not erase the stored one", async () => {
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

  it("two sessions of the same account end in the same state in any order", async () => {
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

  it("one user's progress is not visible from another", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await put(h, ada.cookie, { done: ["intro"] });
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: bea.cookie },
    });
    expect(me.body.progress.done).toEqual([]);
  });

  it("DELETE /api/me leaves no row of the user in any table", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await signIn(h, "github", "77"); // another session and another identity, unrelated
    for (const who of [ada, bea]) {
      await put(h, who.cookie, {
        done: ["intro"],
        exercises: {
          "intro/uno": {
            code: "a",
            hints: 0,
            checks: 1,
            passed: false,
            at: 10,
          },
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
    // A second session of Ada, to prove it falls too.
    await signIn(h, "google", "ada");

    const adaId = (await h.db
      .prepare(
        "SELECT user_id FROM identities WHERE provider = 'google' AND subject = 'ada'",
      )
      .first<{ user_id: string }>())!.user_id;
    for (const table of TABLES) {
      if (table === "users") continue;
      // Every table has rows of Ada before deleting.
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
    // What belongs to others stays: Bea, the GitHub user and the anonymous attempt.
    expect(await count(h, "users")).toBe(2);
    expect(await count(h, "lesson_done")).toBe(1);
    expect(await count(h, "attempts", "user_id IS NULL")).toBe(1);
    expect(await count(h, "attempts")).toBe(2);
    // The old cookie is rejected.
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: ada.cookie },
    });
    expect(me.body).toEqual({ signedIn: false });
  });
});

describe("passed follows the server's record", () => {
  const origin = { origin: "http://runner.test" };
  const claim = (exercise: string) => ({
    exercises: {
      [exercise]: { code: "x", hints: 0, checks: 1, passed: true, at: 10 },
    },
  });
  const passedIn = (progress: any) =>
    Object.fromEntries(
      Object.entries<any>(progress.exercises).map(([id, item]) => [
        id,
        item.passed,
      ]),
    );

  async function passedOf(h: Harness, cookie: string) {
    const me = await h.request("GET", "/api/me", { headers: { cookie } });
    return passedIn(me.body.progress);
  }
  const send = (h: Harness, cookie: string, route: string, body: unknown) =>
    h.request(route === "/api/merge" ? "POST" : "PUT", route, {
      headers: { ...origin, cookie },
      body,
    });
  const run = (h: Harness, cookie: string, mode: string, code: string) =>
    h.post(
      { code, mode, exercise: "intro/uno" },
      { headers: signedIn(cookie) },
    );

  it.each(["/api/progress", "/api/merge"])(
    "a client body that claims passed leaves it false (%s)",
    async (route) => {
      const h = await worker();
      const { cookie } = await signIn(h, "google", "sub-1");
      const reply = await send(h, cookie!, route, claim("intro/uno"));
      expect(reply.status).toBe(route === "/api/merge" ? 200 : 204);
      if (route === "/api/merge") {
        expect(reply.body.progress.exercises["intro/uno"].passed).toBe(false);
        expect(reply.body.account).toEqual(expect.any(String));
      }
      expect(await passedOf(h, cookie!)).toEqual({ "intro/uno": false });
    },
  );

  it("a recorded passing check makes it true and the client cannot take it back", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    const other = await signIn(h, "google", "sub-2");
    await send(h, cookie!, "/api/progress", {
      exercises: {
        "intro/uno": { code: "a", hints: 0, checks: 0, passed: false, at: 100 },
      },
    });
    expect((await run(h, cookie!, "check", "print(1)")).body.passed).toBe(true);
    expect(await passedOf(h, cookie!)).toEqual({ "intro/uno": true });
    // A recorded pass does not replace the learner's code or edit order.
    const me = await h.request("GET", "/api/me", {
      headers: { cookie: cookie! },
    });
    expect(me.body.progress.exercises["intro/uno"]).toMatchObject({
      code: "a",
      at: 100,
    });

    await send(h, cookie!, "/api/merge", {
      exercises: {
        "intro/uno": { hints: 0, checks: 0, passed: false, at: 900 },
      },
    });
    await run(h, cookie!, "check", "FALLA");
    expect(await passedOf(h, cookie!)).toEqual({ "intro/uno": true });
    expect(await passedOf(h, other.cookie!)).toEqual({});
  });

  it("only a passing check of a signed-in user records a pass", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    await run(h, cookie!, "run", "print(1)");
    await run(h, cookie!, "check", "FALLA");
    await h.post(
      { code: "print(1)", mode: "check", exercise: "intro/uno" },
      { headers: { "x-turnstile-token": TOKEN } },
    );
    expect(await passedOf(h, cookie!)).toEqual({});
    expect(await count(h, "exercise_state", "passed = 1")).toBe(0);
  });

  it("a guest's merge on sign-in does not grant a pass the server never recorded", async () => {
    const h = await worker();
    const { cookie } = await signIn(h, "google", "sub-1");
    await run(h, cookie!, "check", "print(1)");
    const merged = await send(h, cookie!, "/api/merge", {
      exercises: {
        ...claim("intro/dos").exercises,
        "intro/uno": { hints: 0, checks: 0, passed: false, at: 1 },
      },
    });
    expect(passedIn(merged.body.progress)).toEqual({
      "intro/uno": true,
      "intro/dos": false,
    });
  });
});

describe("daily purge", () => {
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

  it("deletes an attempt older than 180 days and keeps the recent one", async () => {
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

  it("deletes accounts with no visits in 24 months with everything of theirs, and expired sessions", async () => {
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

  it("uses the periods the environment sets", async () => {
    const h = await worker({ vars: { ATTEMPT_RETENTION_DAYS: "10" } });
    const now = Math.floor(Date.now() / 1000);
    await insertAttempt(h, now - 11 * DAY);
    await insertAttempt(h, now - 9 * DAY);
    await h.purge();
    expect(await count(h, "attempts")).toBe(1);
  });
});
