import { afterEach, describe, expect, it } from "vitest";

import {
  type Harness,
  type Options,
  FAIL_SECRET,
  SPENT_SECRET,
  TOKEN,
  VARS,
  clearOfMinuteEnd,
  start,
} from "./harness.ts";
import { signIn } from "./signin.ts";

const open: Harness[] = [];

async function worker(options?: Options): Promise<Harness> {
  const h = await start(options);
  open.push(h);
  return h;
}

afterEach(async () => {
  await Promise.all(open.splice(0).map((h) => h.dispose()));
});

const run = { code: "print(2 + 2)", mode: "run" };
const verified = { headers: { "x-turnstile-token": TOKEN } };

describe("GET /health", () => {
  it("answers without calling the container", async () => {
    const h = await worker();
    const reply = await h.get("/health");
    expect(reply.status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(0);
  });
});

describe("the site and /run in a single Worker", () => {
  it("serves the catalog at / and the course at /qiskit/ without calling the container", async () => {
    const h = await worker();
    const catalog = await h.get("/");
    expect(catalog.status).toBe(200);
    expect(catalog.headers.get("content-type")).toContain("text/html");
    expect(catalog.body).toContain("<title>Rising</title>");
    const course = await h.get("/qiskit/");
    expect(course.status).toBe(200);
    expect(course.body).toContain("<title>Qubit a qubit</title>");
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("serves the lessons and answers 404 to what is not a file", async () => {
    const h = await worker();
    expect((await h.get("/qiskit/lesson.html")).status).toBe(200);
    expect((await h.get("/qiskit/course.json")).body.parts).toBeDefined();
    expect((await h.get("/courses.json")).body[0].slug).toBe("qiskit");
    expect((await h.get("/no-existe.html")).status).toBe(404);
    // The course pages are served under /qiskit/, not at the root.
    expect((await h.get("/lesson.html")).status).toBe(404);
    expect((await h.get("/lessons/p1-quickstart/lesson.json")).status).toBe(
      404,
    );
  });

  it("runs the code and returns the runner's JSON with the test token", async () => {
    const h = await worker();
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(200);
    expect(reply.body).toMatchObject({
      passed: true,
      error: null,
      tests: [],
      killed: null,
    });
    expect(reply.body.stdout).toBe("recibidos 12 caracteres\n");
    expect(reply.headers.get("set-cookie")).toContain("qg_session=");
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("answers 403 turnstile_missing with the site key when there is no token", async () => {
    const h = await worker();
    const reply = await h.post(run);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_missing");
    expect(reply.body.sitekey).toBe(VARS.TURNSTILE_SITE_KEY);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("answers 500 if the site key is missing, because the page could not pass Turnstile", async () => {
    const h = await worker({ vars: { TURNSTILE_SITE_KEY: "" } });
    const reply = await h.post(run);
    expect(reply.status).toBe(500);
    expect(reply.body.reason).toBe("internal_error");
    expect(reply.body.sitekey).toBeUndefined();
  });
});

describe("per-IP limit", () => {
  it("answers 429 with Retry-After when the per-minute limit is passed", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "3" } });
    for (let i = 0; i < 3; i++)
      expect((await h.post(run, verified)).status).toBe(200);

    const reply = await h.post(run, verified);
    expect(reply.status).toBe(429);
    expect(reply.body.reason).toBe("rate_minute");
    expect(reply.body.error).toMatch(/Espera \d+ s/);
    const retryAfter = Number(reply.headers.get("retry-after"));
    expect(Number.isInteger(retryAfter)).toBe(true);
    expect(retryAfter).toBeGreaterThanOrEqual(1);
    expect(retryAfter).toBeLessThanOrEqual(60);
    expect(h.runnerCalls()).toHaveLength(3);
  });

  it("with simultaneous requests it lets exactly the limit through", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "3" } });
    const replies = await Promise.all(
      Array.from({ length: 10 }, () => h.post(run, verified)),
    );
    expect(replies.filter((reply) => reply.status === 200)).toHaveLength(3);
    expect(replies.filter((reply) => reply.status === 429)).toHaveLength(7);
  });

  it("counts each IP separately", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "1" } });
    expect(
      (await h.post(run, { ...verified, ip: "198.51.100.1" })).status,
    ).toBe(200);
    expect(
      (await h.post(run, { ...verified, ip: "198.51.100.1" })).status,
    ).toBe(429);
    expect(
      (await h.post(run, { ...verified, ip: "198.51.100.2" })).status,
    ).toBe(200);
  });

  it("answers 429 with Retry-After when the daily limit is passed", async () => {
    const h = await worker({ vars: { RATE_PER_DAY: "2" } });
    await h.post(run, verified);
    await h.post(run, verified);

    const reply = await h.post(run, verified);
    expect(reply.status).toBe(429);
    expect(reply.body.reason).toBe("rate_day");
    const retryAfter = Number(reply.headers.get("retry-after"));
    expect(retryAfter).toBeGreaterThanOrEqual(1);
    expect(retryAfter).toBeLessThanOrEqual(86_400);
    expect(h.runnerCalls()).toHaveLength(2);
  });

  it("also limits the requests that Turnstile rejects", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "2" } });
    expect((await h.post(run)).status).toBe(403);
    expect((await h.post(run)).status).toBe(403);
    expect((await h.post(run)).status).toBe(429);
  });
});

describe("Turnstile", () => {
  it("answers 403 without a token and does not reach the container", async () => {
    const h = await worker();
    const reply = await h.post(run);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_missing");
    expect(h.runnerCalls()).toHaveLength(0);
    expect(h.siteverify.calls).toHaveLength(0);
  });

  it("answers 403 with a token that Turnstile rejects", async () => {
    const h = await worker({ vars: { TURNSTILE_SECRET: FAIL_SECRET } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_failed");
    expect(reply.headers.get("set-cookie")).toBeNull();
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("answers 403 with a token already used", async () => {
    const h = await worker({ vars: { TURNSTILE_SECRET: SPENT_SECRET } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_failed");
  });

  it("answers 503 if Turnstile does not respond", async () => {
    const h = await worker({ siteverify: "down" });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(503);
    expect(reply.body.reason).toBe("turnstile_unavailable");
    expect(reply.headers.get("retry-after")).toBe("10");
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("verifies once and then lets requests through with the session cookie", async () => {
    const h = await worker();
    const first = await h.post(run, verified);
    expect(first.status).toBe(200);
    expect(first.body.passed).toBe(true);
    const cookie = first.headers.get("set-cookie") ?? "";
    expect(cookie).toMatch(
      /^qg_session=\d+\.[0-9a-f]{64}; Max-Age=28800; Path=\/run; HttpOnly; Secure; SameSite=Strict$/,
    );

    const second = await h.post(run, {
      headers: { cookie: cookie.split(";")[0] },
    });
    expect(second.status).toBe(200);
    expect(second.headers.get("set-cookie")).toBeNull();
    expect(h.siteverify.calls).toHaveLength(1);
  });

  it("sends Turnstile only the secret and the token", async () => {
    const h = await worker();
    await h.post(run, { ...verified, ip: "203.0.113.50" });
    expect(h.siteverify.calls).toHaveLength(1);
    expect(Object.keys(h.siteverify.calls[0]).toSorted()).toEqual([
      "response",
      "secret",
    ]);
  });

  it("rejects a tampered cookie, one from another IP, or an expired one", async () => {
    const h = await worker({ vars: { SESSION_HOURS: "0.00001" } });
    const issued =
      (await h.post(run, verified)).headers.get("set-cookie") ?? "";
    const cookie = issued.split(";")[0];
    const tag = cookie.slice(-64);

    const forged = cookie.replace(tag, "0".repeat(64));
    expect((await h.post(run, { headers: { cookie: forged } })).status).toBe(
      403,
    );

    const other = await h.post(run, {
      ip: "198.51.100.99",
      headers: { cookie },
    });
    expect(other.status).toBe(403);

    await new Promise((resolve) => setTimeout(resolve, 150));
    const expired = await h.post(run, { headers: { cookie } });
    expect(expired.status).toBe(403);
    expect(expired.body.reason).toBe("turnstile_missing");
  });

  it("accepts the cookie until it expires", async () => {
    const h = await worker();
    const cookie = (
      (await h.post(run, verified)).headers.get("set-cookie") ?? ""
    ).split(";")[0];
    expect((await h.post(run, { headers: { cookie } })).status).toBe(200);
  });
});

describe("code size", () => {
  const limit = 20_000;

  it("answers 413 without reaching the container", async () => {
    const h = await worker();
    const reply = await h.post(
      { code: "x".repeat(limit + 1), mode: "run" },
      verified,
    );
    expect(reply.status).toBe(413);
    expect(reply.body.reason).toBe("too_large");
    expect(reply.body.error).toContain("20000");
    expect(h.runnerCalls()).toHaveLength(0);
    expect(h.siteverify.calls).toHaveLength(0);
  });

  it("counts bytes, not characters", async () => {
    const h = await worker();
    const code = "é".repeat(limit / 2 + 1);
    expect(code).toHaveLength(limit / 2 + 1);
    expect((await h.post({ code, mode: "run" }, verified)).status).toBe(413);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("lets through a code of exactly the maximum", async () => {
    const h = await worker();
    const reply = await h.post(
      { code: "x".repeat(limit), mode: "run" },
      verified,
    );
    expect(reply.status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("answers 413 to a huge body without reading all of it", async () => {
    const h = await worker();
    // Only the header: the 413 arrives without the body having been sent.
    const status = await h.declare("POST", "/run", 6 * limit + 1025, {
      ...verified.headers,
      "content-type": "application/json",
    });
    expect(status).toBe(413);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("answers 400 to invalid JSON or JSON without code", async () => {
    const h = await worker();
    expect(
      (await h.post(null, { ...verified, raw: "{no es json" })).status,
    ).toBe(400);
    expect((await h.post({ mode: "run" }, verified)).status).toBe(400);
    expect((await h.post({ code: 3 }, verified)).status).toBe(400);
    expect(h.runnerCalls()).toHaveLength(0);
  });
});

// The test prices are those of `standard-2` with a `sleepAfter` of 35 s:
// 20,000 nanodollars per CPU second and 15,840 per second on (6 GiB and
// 12 GB). An isolated 2 s run costs 2 × 20,000 for CPU and 37 × 15,840 for the
// instance being on, which is 626,080. Reserving an isolated run sets aside
// 30 × 20,000 + 65 × 15,840 = 1,629,600. The Worker sends every run to
// instance 0, so a run is isolated when `QUIET_MS` have passed since the last.
const CLOCK = "2026-10-15T12:00:00Z";
const ISOLATED_2S = 626_080;
const QUIET_MS = 600_000;

const work = (ms: number) => ({ code: `TRABAJO-${ms}`, mode: "run" });

function costs(h: Harness): number[] {
  return h
    .workerLogs()
    .map((line) => JSON.parse(line))
    .filter((line) => line.event === "run" && line.cost_nano_usd !== undefined)
    .map((line) => line.cost_nano_usd);
}

describe("monthly budget", () => {
  // With a reservation of 0.05 s a run that hangs is stopped at 50 ms;
  // without a cap it would cost the 1500 ms it takes.
  const hang = { code: "colgar", mode: "run" };

  it("charges the on-window of an isolated run and only the extension of the next one", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    await h.post(work(2000), verified);
    // Inside the first run's window: 1 s of CPU and the second that extends the
    // on-window (1 × 20,000 + 1 × 15,840).
    await h.post(work(1000), verified);
    // Once the window has passed, instance 0 shut down and is charged in full again.
    await h.advance(QUIET_MS);
    await h.post(work(2000), verified);

    expect(costs(h)).toEqual([ISOLATED_2S, 35_840, ISOLATED_2S]);
    // A free instance 0 serves every run, so the window above is shared.
    expect(new Set(h.runnerCalls().map((call) => call.instance))).toEqual(
      new Set(["instance-0"]),
    );
  });

  it.each([
    { type: "lite", nano: 30_805 },
    { type: "standard-1", nano: 410_720 },
    { type: "standard-2", nano: ISOLATED_2S },
    { type: "standard-4", nano: 1_321_800 },
  ])(
    "the price comes from the instance type: $type",
    async ({ type, nano }) => {
      const h = await worker({
        vars: { FAKE_CLOCK: CLOCK, INSTANCE_TYPE: type },
      });
      await h.post(work(2000), verified);
      expect(costs(h)).toEqual([nano]);
    },
  );

  it("answers 500 with an instance type that does not exist", async () => {
    const h = await worker({ vars: { INSTANCE_TYPE: "gigante" } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(500);
    expect(h.workerLogs().join("\n")).toContain("INSTANCE_TYPE");
  });

  it("stops a run that exceeds what was set aside and charges no more than the reservation", async () => {
    // The reservation is 0.05 × 20,000 for CPU and 35.05 × 15,840 for the instance being on.
    const reserved = 556_192;
    const h = await worker({ vars: { RESERVED_BUSY_SECONDS: "0.05" } });
    const reply = await h.post(hang, verified);
    expect(reply.status).toBe(504);
    expect(reply.body.reason).toBe("run_too_long");
    expect(h.runnerStops()).toBe(1);

    const line = h
      .workerLogs()
      .map((entry) => JSON.parse(entry))
      .find((entry) => entry.outcome === "run_too_long");
    expect(line.busy_ms).toBeLessThan(1000);
    // What is charged is the window set aside, not the one the job would have lasted.
    expect(line.cost_nano_usd).toBeLessThanOrEqual(reserved);
    expect(line.cost_nano_usd).toBeGreaterThan(500_000);
  });

  it("when the cap is reached it stops only the request's instance, not the one serving another learner", async () => {
    // The first attempt lands on instance 0, which serves another learner and answers
    // 503; the retry lands on 1, where the job hangs.
    const h = await worker({ vars: { RESERVED_BUSY_SECONDS: "0.4" } });
    const other = h.get("/other-learner");
    while (h.runnerCalls().length < 1)
      await new Promise((resolve) => setTimeout(resolve, 10));

    const reply = await h.post(hang, verified);
    expect(reply.status).toBe(504);
    expect(reply.body.reason).toBe("run_too_long");
    // The other learner's job, the first attempt (503) and the retry.
    expect(h.runnerCalls().map((call) => call.instance)).toEqual([
      "instance-0",
      "instance-0",
      "instance-1",
    ]);
    expect(h.runnerStops()).toBe(1);

    const finished = await other;
    expect(finished.status).toBe(200);
    expect(finished.body.passed).toBe(true);
  });

  it("does not run if the reservation for a run no longer fits", async () => {
    // With 0.001 USD the public has 750,000 nanodollars and the reservation for one
    // isolated run is 1,629,600.
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.001" } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(503);
    expect(reply.body.reason).toBe("budget");
    expect(reply.body.error).toContain("mes");
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("with room for a single run, of several simultaneous ones only one reaches the container", async () => {
    // The public has 2,100,000 nanodollars: one isolated reservation fits
    // (1,629,600) and no other: the next sets aside 600,000 of CPU more.
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.0028" } });
    const replies = await Promise.all(
      Array.from({ length: 8 }, () => h.post(run, verified)),
    );

    expect(replies.filter((reply) => reply.status === 200)).toHaveLength(1);
    const refused = replies.filter((reply) => reply.status === 503);
    expect(refused).toHaveLength(7);
    for (const reply of refused) expect(reply.body.reason).toBe("budget");
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("on finishing it swaps the reservation for the measured cost and leaves room for the next one", async () => {
    // The public has 2,475,000 nanodollars. Each isolated run sets aside
    // 1,629,600 and the first spends 554,400 (the clock does not advance):
    // the second fits only if the first returned what it did not spend.
    const h = await worker({
      vars: { MONTHLY_BUDGET_USD: "0.0033", FAKE_CLOCK: CLOCK },
    });
    expect((await h.post(run, verified)).status).toBe(200);
    await h.advance(QUIET_MS);
    expect((await h.post(run, verified)).status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(2);
    expect(costs(h)).toEqual([554_400, 554_400]);
  });

  it("returns the reservation if Turnstile rejects the request", async () => {
    // The public has 2,250,000 nanodollars: one reservation fits, not two.
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.003" } });
    for (let i = 0; i < 3; i++) expect((await h.post(run)).status).toBe(403);
    expect((await h.post(run, verified)).status).toBe(200);
  });

  it("spends no Turnstile verification when there is no budget left", async () => {
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.001" } });
    expect((await h.post(run, verified)).status).toBe(503);
    expect(h.siteverify.calls).toHaveLength(0);
  });

  it("keeps running while the spend is under the budget", async () => {
    const h = await worker();
    for (let i = 0; i < 5; i++)
      expect((await h.post(run, verified)).status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(5);
  });

  it("a failure to record the cost does not change the response of a successful run", async () => {
    const h = await worker({ vars: { FAKE_SETTLE_FAILS: "1" } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(200);
    expect(reply.body.passed).toBe(true);
    const lines = h.workerLogs().map((line) => JSON.parse(line));
    expect(lines.filter((line) => line.where === "settle")).toHaveLength(1);
  });

  it("a failure to record the cost does not hide the container's error", async () => {
    const h = await worker({ vars: { FAKE_SETTLE_FAILS: "1" } });
    const reply = await h.post({ code: "romper-contenedor" }, verified);
    expect(reply.status).toBe(500);
    expect(reply.body.reason).toBe("internal_error");
    // Two lines remain: the one for the failed adjustment and the one for the request's error.
    const lines = h.workerLogs().map((line) => JSON.parse(line));
    expect(lines.filter((line) => line.where === "settle")).toHaveLength(1);
    expect(
      lines.filter((line) => line.outcome === "internal_error" && !line.where),
    ).toHaveLength(1);
  });
});

describe("budget caps", () => {
  const MAINTAINER = "1001";

  async function maintainer(h: Harness) {
    const { cookie } = await signIn(h, "github", MAINTAINER);
    return { headers: { cookie: cookie! } };
  }

  it("the public stops at 75 % of the budget and a maintainer carries on to 100 %", async () => {
    // The public has 2,775,000 of the 3,700,000 nanodollars. Two isolated 2 s
    // runs spend 1,252,160 and the reservation of a third (1,629,600) exceeds
    // 75 % but not the total.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.0037",
        MAINTAINERS: MAINTAINER,
        FAKE_CLOCK: CLOCK,
      },
    });
    const staff = await maintainer(h);
    expect((await h.post(work(2000), verified)).status).toBe(200);
    await h.advance(QUIET_MS);
    expect((await h.post(work(2000), verified)).status).toBe(200);
    await h.advance(QUIET_MS);

    const refused = await h.post(work(1000), verified);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget");

    const allowed = await h.post(work(1000), staff);
    expect(allowed.status).toBe(200);
    expect(h.siteverify.calls).toHaveLength(2);
    // 1 s of CPU and the 36 s the instance is on.
    expect(costs(h)).toEqual([ISOLATED_2S, ISOLATED_2S, 590_240]);

    // Another month starts: the public can run again.
    await h.advance(20 * 86_400_000);
    expect((await h.post(work(1000), verified)).status).toBe(200);
  });

  it("the public stops at its daily cap, a maintainer does not, and the next day it resumes", async () => {
    // 1/10 of the public's 20,025,000 is 2,002,500 per day: one isolated run fits
    // (626,080 spent) and the reservation of another (1,629,600) does not.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.0267",
        PUBLIC_BUDGET_DAYS: "10",
        MAINTAINERS: MAINTAINER,
        FAKE_CLOCK: CLOCK,
      },
    });
    const staff = await maintainer(h);
    expect((await h.post(work(2000), verified)).status).toBe(200);
    await h.advance(QUIET_MS);

    const refused = await h.post(work(2000), verified);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget_day");
    expect(refused.body.error).toContain("hoy");
    // 12 h minus the run's 2 s and the 10 minutes remain until UTC midnight.
    expect(refused.headers.get("retry-after")).toBe("42598");

    expect((await h.post(work(2000), staff)).status).toBe(200);

    await h.advance(13 * 3_600_000);
    expect((await h.post(work(2000), verified)).status).toBe(200);
  });

  it("at 100 % not even a maintainer runs", async () => {
    // An isolated run spends 554,400 and the next sets aside 1,629,600: 2,184,000
    // exceeds the budget's 2,000,000.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.002",
        MAINTAINERS: MAINTAINER,
        FAKE_CLOCK: CLOCK,
      },
    });
    const staff = await maintainer(h);
    expect((await h.post(run, staff)).status).toBe(200);
    await h.advance(QUIET_MS);

    const refused = await h.post(run, staff);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget");
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("if the adjustment fails the spend stays at what was set aside and can only be over", async () => {
    // With the adjustment, two isolated runs spend 554,400 and set aside 1,629,600:
    // 2,184,000 fits in the public's 3,000,000. Without it, the first stays
    // at 1,629,600 and the second does not fit.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.004",
        FAKE_SETTLE_FAILS: "1",
        FAKE_CLOCK: CLOCK,
      },
    });
    expect((await h.post(run, verified)).status).toBe(200);
    await h.advance(QUIET_MS);
    const refused = await h.post(run, verified);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget");
  });
});

describe("what the container receives", () => {
  it("only the body type: no cookie, no IP, no token", async () => {
    const h = await worker();
    const first = await h.post(run, { ...verified, ip: "203.0.113.50" });
    const cookie = (first.headers.get("set-cookie") ?? "").split(";")[0];
    await h.post(run, {
      ip: "203.0.113.50",
      headers: { cookie, "user-agent": "prueba" },
    });

    const calls = h.runnerCalls();
    expect(calls).toHaveLength(2);
    for (const call of calls) {
      expect(call.path).toBe("/run");
      // content-length is only the size of the body that the runtime adds when sending it.
      expect(call.headers.filter((name) => name !== "content-length")).toEqual([
        "content-type",
      ]);
    }
  });
});

describe("logging", () => {
  const MARK = "MARCA_SECRETA_DEL_CODIGO";
  const IP = "203.0.113.77";

  it("stores no code, IP, token or cookie on any path", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "5" } });
    const code = `print("${MARK}")`;
    const cookie = (
      (
        await h.post(
          { code, mode: "check", exercise: "p1-quickstart/ghz" },
          { ...verified, ip: IP },
        )
      ).headers.get("set-cookie") ?? ""
    ).split(";")[0];

    await h.post(
      { code, mode: "check", exercise: "p1-quickstart/ghz" },
      { ip: IP, headers: { cookie } },
    );
    await h.post(
      { code: code + "x".repeat(20_000) },
      { ip: IP, headers: { cookie } },
    );
    await h.post(null, {
      ip: IP,
      headers: { cookie },
      raw: `{"code": "${MARK}`,
    });
    await h.post({ code, mode: MARK, exercise: `${MARK}/${MARK}` }, { ip: IP });
    const limited = await h.post({ code }, { ip: IP, headers: { cookie } });
    expect(limited.status).toBe(429);

    const lines = h.workerLogs();
    expect(lines.length).toBeGreaterThanOrEqual(6);
    const everything = lines.join("\n");
    for (const secret of [
      MARK,
      IP,
      TOKEN,
      cookie.split("=")[1],
      "198.51.100",
    ]) {
      expect(everything).not.toContain(secret);
    }
    for (const line of lines) {
      const entry = JSON.parse(line);
      expect(entry.event).toBe("run");
      expect(
        Object.keys(entry).every((key) =>
          [
            "event",
            "outcome",
            "status",
            "mode",
            "exercise",
            "code_bytes",
            "busy_ms",
            "cost_nano_usd",
          ].includes(key),
        ),
      ).toBe(true);
    }
  });

  it("an accepted request leaves a line with the result and the cost", async () => {
    const h = await worker();
    await h.post(
      { code: "print(1)", mode: "check", exercise: "p1-quickstart/ghz" },
      verified,
    );
    const [line] = h.workerLogs();
    expect(JSON.parse(line)).toMatchObject({
      event: "run",
      outcome: "ok",
      status: 200,
      mode: "check",
      exercise: "p1-quickstart/ghz",
      code_bytes: 8,
    });
    expect(JSON.parse(line).cost_nano_usd).toBeGreaterThan(0);
  });

  it("an internal error logs the error name and not its text", async () => {
    const h = await worker({
      vars: { RATE_PER_MINUTE: `not a number ${MARK}` },
    });
    const reply = await h.post({ code: "print(1)" }, verified);
    expect(reply.status).toBe(500);
    const lines = h.workerLogs().join("\n");
    expect(lines).toContain("ConfigError");
    expect(lines).toContain("RATE_PER_MINUTE");
    expect(lines).not.toContain(MARK);
  });
});

describe("real Turnstile", async () => {
  // Cloudflare documents these test keys. This test talks to its service.
  const reachable = await fetch(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    {
      method: "POST",
      body: new URLSearchParams({ secret: FAIL_SECRET, response: "x" }),
      signal: AbortSignal.timeout(5000),
    },
  ).then(
    () => true,
    () => false,
  );

  it.skipIf(!reachable)(
    "accepts with the test secret that always passes",
    async () => {
      const h = await worker({ siteverify: "real" });
      expect((await h.post(run, verified)).status).toBe(200);
    },
  );

  it.skipIf(!reachable)(
    "rejects with the test secret that always fails",
    async () => {
      const h = await worker({
        siteverify: "real",
        vars: { TURNSTILE_SECRET: FAIL_SECRET },
      });
      expect((await h.post(run, verified)).status).toBe(403);
    },
  );
});
