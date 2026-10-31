import { afterEach, describe, expect, it } from "vitest";

import {
  type Harness,
  clearOfMinuteEnd,
  start as startWorker,
} from "./harness.ts";
import { signIn } from "./signin.ts";

const open: Harness[] = [];

async function worker(): Promise<Harness> {
  const h = await startWorker({ vars: { FAKE_CLOCK: "2026-10-21T12:00:00Z" } });
  open.push(h);
  return h;
}

afterEach(async () => {
  await Promise.all(open.splice(0).map((h) => h.dispose()));
});

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const DAY = 24 * 60 * MINUTE;
const origin = { origin: "http://runner.test" };

async function begin(h: Harness) {
  const started = await h.request("POST", "/auth/device/code");
  expect(started.status).toBe(200);
  return started.body as {
    deviceCode: string;
    userCode: string;
    verificationUri: string;
    verificationUriComplete: string;
    expiresIn: number;
    interval: number;
  };
}

const poll = (h: Harness, deviceCode: string) =>
  h.request("POST", "/auth/device/token", { body: { deviceCode } });

// The learner in a browser that is signed in.
async function learner(h: Harness, subject = "learner-7c2e91d4") {
  const { cookie } = await signIn(h, "google", subject);
  return {
    cookie: cookie!,
    page: (code: string) =>
      h.request("GET", `/auth/device?code=${code}`, {
        headers: { cookie: cookie! },
      }),
    decide: (code: string, decision: "approve" | "deny") =>
      h.request("POST", "/auth/device/approve", {
        headers: { ...origin, cookie: cookie! },
        form: { code, decision },
      }),
  };
}

async function login(h: Harness) {
  const codes = await begin(h);
  const who = await learner(h);
  expect((await who.decide(codes.userCode, "approve")).status).toBe(200);
  const got = await poll(h, codes.deviceCode);
  expect(got.status).toBe(200);
  return { ...who, codes, token: got.body.token as string };
}

const bearer = (token: string) => ({ authorization: `Bearer ${token}` });
const me = (h: Harness, token: string) =>
  h.request("GET", "/api/me", { headers: bearer(token) });

describe("device flow", () => {
  it("approve: the CLI collects a token that reads /api/me and posts XP", async () => {
    const h = await worker();
    const codes = await begin(h);
    expect(codes.userCode).toMatch(/^[A-Z2-9]{4}-[A-Z2-9]{4}$/);
    expect(codes.verificationUri).toBe("http://runner.test/auth/device");
    expect(codes.verificationUriComplete).toBe(
      `http://runner.test/auth/device?code=${codes.userCode}`,
    );

    expect((await poll(h, codes.deviceCode)).body.reason).toBe(
      "authorization_pending",
    );

    const signedOut = await h.request(
      "GET",
      `/auth/device?code=${codes.userCode}`,
    );
    expect(signedOut.status).toBe(200);
    expect(signedOut.body).toContain("/auth/google?return=");

    const who = await learner(h);
    const confirm = await who.page(codes.userCode);
    expect(confirm.body).toContain(codes.userCode);
    expect(confirm.body).toContain('value="approve"');
    expect(confirm.headers.get("content-security-policy")).toContain(
      "frame-ancestors 'none'",
    );
    expect((await who.decide(codes.userCode, "approve")).status).toBe(200);

    await h.advance(codes.interval * SECOND);
    const got = await poll(h, codes.deviceCode);
    expect(got.status).toBe(200);
    expect(got.body.token).toMatch(/^rs_[A-Za-z0-9_-]{43}$/);
    expect(got.body.expiresAt).toBe(
      Date.parse("2026-10-21T12:00:05Z") + 90 * DAY,
    );

    const token = got.body.token as string;
    const profile = await me(h, token);
    expect(profile.body).toMatchObject({
      signedIn: true,
      providers: ["google"],
    });
    // No Origin header: a bearer request is not a browser request.
    const granted = await h.request("POST", "/api/xp", {
      headers: bearer(token),
      body: { source: "cli", ref: "p1-quickstart:ghz", amount: 10 },
    });
    expect(granted.body).toMatchObject({ granted: 10, total: 10 });
    const today = await h.request("GET", "/api/xp", {
      headers: bearer(token),
    });
    expect(today.body).toEqual({ total: 10, cap: 300 });
  });

  it("stores only hashes of both codes and of the token", async () => {
    const h = await worker();
    const { codes, token } = await login(h);
    const rows = await h.db
      .prepare(
        `SELECT device_hash AS a, user_hash AS b FROM device_codes
         UNION ALL SELECT token_hash, kind FROM sessions`,
      )
      .all<{ a: string; b: string }>();
    expect(JSON.stringify(rows.results)).not.toContain(codes.deviceCode);
    expect(JSON.stringify(rows.results)).not.toContain(token);
    expect(JSON.stringify(rows.results)).not.toContain(codes.userCode);
  });

  it("deny: the CLI is refused and the code is spent", async () => {
    const h = await worker();
    const codes = await begin(h);
    const who = await learner(h);
    expect((await who.decide(codes.userCode, "deny")).status).toBe(200);

    await h.advance(codes.interval * SECOND);
    const refused = await poll(h, codes.deviceCode);
    expect(refused.status).toBe(403);
    expect(refused.body.reason).toBe("access_denied");

    await h.advance(codes.interval * SECOND);
    expect((await poll(h, codes.deviceCode)).body.reason).toBe("invalid_code");
    const sessions = await h.db
      .prepare("SELECT COUNT(*) AS n FROM sessions WHERE kind = 'cli'")
      .first<{ n: number }>();
    expect(sessions!.n).toBe(0);
  });

  it("expiry: an old code cannot be approved or collected", async () => {
    const h = await worker();
    const codes = await begin(h);
    const who = await learner(h);
    await h.advance(codes.expiresIn * SECOND + SECOND);

    const late = await who.decide(codes.userCode, "approve");
    expect(late.status).toBe(410);
    const polled = await poll(h, codes.deviceCode);
    expect(polled.status).toBe(400);
    expect(polled.body.reason).toBe("expired_code");
  });

  it("a code approved in time but collected late still expires", async () => {
    const h = await worker();
    const codes = await begin(h);
    const who = await learner(h);
    await who.decide(codes.userCode, "approve");
    await h.advance(codes.expiresIn * SECOND + SECOND);
    expect((await poll(h, codes.deviceCode)).body.reason).toBe("expired_code");
  });

  it("reused code: a second poll and a second approval get nothing", async () => {
    const h = await worker();
    const { codes, token, ...who } = await login(h);

    await h.advance(codes.interval * SECOND);
    const again = await poll(h, codes.deviceCode);
    expect(again.status).toBe(400);
    expect(again.body.reason).toBe("invalid_code");
    expect((await me(h, token)).status).toBe(200);

    const approvedTwice = await who.decide(codes.userCode, "approve");
    expect(approvedTwice.status).toBe(404);

    const other = await begin(h);
    expect((await who.decide(other.userCode, "approve")).status).toBe(200);
    expect((await who.decide(other.userCode, "deny")).status).toBe(409);
    await h.advance(other.interval * SECOND);
    expect((await poll(h, other.deviceCode)).status).toBe(200);
  });

  it("polling faster than the interval gets 429 slow_down", async () => {
    const h = await worker();
    const codes = await begin(h);
    expect((await poll(h, codes.deviceCode)).status).toBe(400);
    const fast = await poll(h, codes.deviceCode);
    expect(fast.status).toBe(429);
    expect(fast.body.reason).toBe("slow_down");
    expect(fast.headers.get("retry-after")).toBe(String(codes.interval));
    await h.advance(codes.interval * SECOND);
    expect((await poll(h, codes.deviceCode)).body.reason).toBe(
      "authorization_pending",
    );
  });

  it("a poll does not count against the per-IP limit of /auth", async () => {
    // The limiter's alarm fires at once under a fake clock earlier than the
    // real date, so this test runs on the real one.
    await clearOfMinuteEnd();
    const h = await startWorker({ vars: { AUTH_PER_MINUTE: "2" } });
    open.push(h);
    const codes = await begin(h);
    const statuses: number[] = [];
    for (let polls = 0; polls < 5; polls++) {
      // The interval is not under test: let every poll through.
      // oxlint-disable-next-line eslint/no-await-in-loop -- Each poll follows the reset.
      await h.db.prepare("UPDATE device_codes SET polled_at = 0").run();
      // oxlint-disable-next-line eslint/no-await-in-loop -- Each poll follows the reset.
      statuses.push((await poll(h, codes.deviceCode)).status);
    }
    expect(statuses).toEqual([400, 400, 400, 400, 400]);
    expect((await h.request("POST", "/auth/device/code")).status).toBe(200);
    expect((await h.request("POST", "/auth/device/code")).status).toBe(429);
  });

  describe("approval refuses", () => {
    it.each([
      ["a signed-out browser", { cookie: "" }, 401],
      ["a request from another origin", { origin: "http://evil.test" }, 403],
    ])("%s", async (_, headers, status) => {
      const h = await worker();
      const codes = await begin(h);
      const who = await learner(h);
      const refused = await h.request("POST", "/auth/device/approve", {
        headers: { ...origin, cookie: who.cookie, ...headers },
        form: { code: codes.userCode, decision: "approve" },
      });
      expect(refused.status).toBe(status);
      await h.advance(codes.interval * SECOND);
      expect((await poll(h, codes.deviceCode)).body.reason).toBe(
        "authorization_pending",
      );
    });

    it.each([
      ["a code that does not exist", "ZZZZ-ZZZZ", 404],
      ["a malformed code", "abc", 400],
    ])("%s", async (_, code, status) => {
      const h = await worker();
      const who = await learner(h);
      expect((await who.decide(code, "approve")).status).toBe(status);
    });
  });

  it("the page escapes what it is given", async () => {
    const h = await worker();
    const who = await learner(h);
    const page = await h.request(
      "GET",
      `/auth/device?code=${encodeURIComponent('"><script>x</script>')}`,
      { headers: { cookie: who.cookie } },
    );
    expect(page.status).toBe(400);
    expect(page.body).not.toContain("<script>");
  });
});

describe("bearer token", () => {
  it("revoke: the logout kills the token and leaves other tokens", async () => {
    const h = await worker();
    const first = await login(h);
    const second = await login(h);

    const out = await h.request("POST", "/auth/logout", {
      headers: bearer(first.token),
    });
    expect(out.status).toBe(204);
    const dead = await me(h, first.token);
    expect(dead.status).toBe(401);
    expect(dead.body.reason).toBe("token_invalid");
    expect((await me(h, second.token)).status).toBe(200);
    // Revoking again, or with a token nobody has, is not an error.
    expect(
      (
        await h.request("POST", "/auth/logout", {
          headers: bearer(first.token),
        })
      ).status,
    ).toBe(204);
  });

  it("expired: a token past CLI_TOKEN_DAYS gets 401", async () => {
    const h = await worker();
    const { token } = await login(h);
    await h.advance(89 * DAY);
    expect((await me(h, token)).status).toBe(200);
    await h.advance(2 * DAY);
    const dead = await me(h, token);
    expect(dead.status).toBe(401);
    expect(dead.body.reason).toBe("token_invalid");
  });

  it("the purge deletes expired tokens and unanswered codes", async () => {
    const h = await worker();
    const { token } = await login(h);
    await begin(h);
    await h.advance(91 * DAY);
    await h.purge(new Date(Date.parse("2026-10-21T12:00:00Z") + 91 * DAY));
    const left = await h.db
      .prepare(
        `SELECT (SELECT COUNT(*) FROM device_codes) AS codes,
                (SELECT COUNT(*) FROM sessions WHERE kind = 'cli') AS tokens`,
      )
      .first<{ codes: number; tokens: number }>();
    expect(left).toEqual({ codes: 0, tokens: 0 });
    expect((await me(h, token)).status).toBe(401);
  });

  describe("is judged by the token alone", () => {
    it.each([
      ["no such token", "Bearer rs_nothing"],
      ["another scheme", "Basic abc"],
      ["an empty token", "Bearer "],
    ])("%s gets 401", async (_, header) => {
      const h = await worker();
      const who = await learner(h);
      // A valid cookie does not rescue a request with a bad Authorization.
      const refused = await h.request("GET", "/api/me", {
        headers: { authorization: header, cookie: who.cookie },
      });
      expect(refused.status).toBe(401);
      expect(refused.body.reason).toBe("token_invalid");
    });

    it("a web session token is not a bearer token, nor the reverse", async () => {
      const h = await worker();
      const { token } = await login(h);
      const { cookie } = await learner(h, "someone-else-51d0");
      const session = cookie.split("=")[1];
      expect((await me(h, session)).status).toBe(401);
      const asCookie = await h.request("GET", "/api/me", {
        headers: { cookie: `qg_auth=${token}` },
      });
      expect(asCookie.body).toEqual({ signedIn: false });
    });

    it("a cookie request still needs the Origin header", async () => {
      const h = await worker();
      const who = await learner(h);
      const forged = await h.request("POST", "/api/xp", {
        headers: { cookie: who.cookie },
        body: { source: "cli", ref: "a", amount: 1 },
      });
      expect(forged.status).toBe(403);
    });
  });

  it("the per-user limit applies to a bearer request", async () => {
    await clearOfMinuteEnd();
    const h = await startWorker({ vars: { RATE_PER_MINUTE: "2" } });
    open.push(h);
    const { token } = await login(h);
    const statuses: number[] = [];
    for (let call = 0; call < 3; call++) {
      // oxlint-disable-next-line eslint/no-await-in-loop -- The calls count in order.
      statuses.push((await me(h, token)).status);
    }
    expect(statuses).toEqual([200, 200, 429]);
  });
});
