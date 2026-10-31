import { afterEach, describe, expect, it } from "vitest";

import { base64url, fromBase64url } from "../src/account.ts";
import { type Harness, type Options, PUSH_HOST, start } from "./harness.ts";
import { signIn } from "./signin.ts";
import { vapidKeys } from "./vapid.ts";

const open: Harness[] = [];
afterEach(async () => {
  await Promise.all(open.splice(0).map((h) => h.dispose()));
});

const HOUR = 3_600_000;
const DAY = 24 * HOUR;
// The fixture starts on the evening of a Tuesday, UTC.
const TUESDAY = "2026-10-20T12:00:00Z";
const SUBJECT = "mailto:ops@example.test";

async function worker(vars: Options["vars"] = {}): Promise<Harness> {
  const h = await start({
    vars: {
      FAKE_CLOCK: TUESDAY,
      ...(await vapidKeys()),
      VAPID_SUBJECT: SUBJECT,
      ...vars,
    },
  });
  open.push(h);
  return h;
}

interface Who {
  name: string;
  cookie: string;
}

async function user(h: Harness, name: string): Promise<Who> {
  const { cookie } = await signIn(h, "google", `subject-${name}-8c1f2d9a`);
  return { name, cookie: cookie! };
}

const call = (
  h: Harness,
  who: Who,
  method: string,
  pathname: string,
  body?: unknown,
) =>
  h.request(method, pathname, {
    headers: { origin: "http://runner.test", cookie: who.cookie },
    body,
  });

// A browser's subscription: a real P-256 key and a 16-byte secret, as the
// encryption of the message needs.
async function browser(path: string) {
  const pair = (await crypto.subtle.generateKey(
    { name: "ECDH", namedCurve: "P-256" },
    true,
    ["deriveBits"],
  )) as CryptoKeyPair;
  const raw = new Uint8Array(
    (await crypto.subtle.exportKey("raw", pair.publicKey)) as ArrayBuffer,
  );
  return {
    endpoint: `https://${PUSH_HOST}${path}`,
    keys: {
      p256dh: base64url(raw),
      auth: base64url(crypto.getRandomValues(new Uint8Array(16))),
    },
  };
}

async function subscribe(h: Harness, who: Who, path: string) {
  const reply = await call(h, who, "POST", "/api/push", await browser(path));
  expect(reply.status).toBe(204);
  return `https://${PUSH_HOST}${path}`;
}

const earn = (h: Harness, who: Who, tz: string, ref = "d1") =>
  call(h, who, "POST", "/api/xp", { source: "drill", ref, amount: 5, tz });

// The 17th minute of every UTC hour from `from` to `to`, as the cron fires.
async function sweep(h: Harness, from: string, hours: number) {
  const reached: { at: string; endpoints: string[] }[] = [];
  for (let k = 0; k < hours; k++) {
    const at = new Date(Date.parse(from) + k * HOUR);
    const before = h.pushes.length;
    await h.remind(at);
    const endpoints = h.pushes.slice(before).map((p) => p.endpoint);
    if (endpoints.length) reached.push({ at: at.toISOString(), endpoints });
  }
  return reached;
}

describe("streak reminder", () => {
  it("reaches each learner at 19:00 in their own zone and only if today has no XP", async () => {
    const h = await worker();
    const zones = {
      tokyo: "Asia/Tokyo",
      kolkata: "Asia/Kolkata",
      madrid: "Europe/Madrid",
      lima: "America/Lima",
      early: "Asia/Tokyo",
      busy: "Europe/Madrid",
    };
    const who: Record<string, Who> = {};
    const endpoint: Record<string, string> = {};
    for (const [name, zone] of Object.entries(zones)) {
      who[name] = await user(h, name);
      endpoint[name] = await subscribe(h, who[name], `/${name}`);
      // Tuesday 12:00 UTC: a day in each zone, ahead of the day tested.
      expect((await earn(h, who[name], zone)).status).toBe(200);
    }
    // Wednesday 05:00 UTC, which is Wednesday afternoon in Tokyo and morning in
    // Madrid: only `early` and `busy` earn again.
    await h.advance(DAY - 7 * HOUR);
    await earn(h, who.busy, zones.busy, "d2");
    await earn(h, who.early, zones.early, "d2");

    // Wednesday 00:17 UTC to Thursday 00:17 UTC, one sweep per hour.
    const reached = await sweep(h, "2026-10-21T00:17:00Z", 25);
    expect(reached).toEqual([
      // 19:17 Wednesday in Tokyo; `early` earned at 14:00 and is left alone.
      {
        at: "2026-10-21T10:17:00.000Z",
        endpoints: [endpoint.tokyo],
      },
      // 19:47 in Kolkata, UTC+5:30: the hour is 19 from 13:30 to 14:30 UTC.
      { at: "2026-10-21T14:17:00.000Z", endpoints: [endpoint.kolkata] },
      // 19:17 in Madrid, UTC+2; `busy` earned at 07:00.
      { at: "2026-10-21T17:17:00.000Z", endpoints: [endpoint.madrid] },
      // 19:17 Wednesday in Lima, UTC-5.
      { at: "2026-10-22T00:17:00.000Z", endpoints: [endpoint.lima] },
    ]);
  });

  it("sends the learner's streak once, with an encrypted body and a VAPID identity", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const url = await subscribe(h, ada, "/ada");
    await earn(h, ada, "UTC");
    await h.advance(DAY);

    // 19:17 UTC, and again 5 minutes later in the same hour.
    await h.remind(new Date("2026-10-21T19:17:00Z"));
    await h.remind(new Date("2026-10-21T19:22:00Z"));

    expect(h.pushes).toHaveLength(1);
    const [push] = h.pushes;
    expect(push.endpoint).toBe(url);
    expect(push.headers["content-encoding"]).toBe("aes128gcm");
    // A push service checks the token against the key it names.
    const [, token, key] =
      /^vapid t=([\w.-]+), k=([\w-]+)$/.exec(push.headers.authorization) ?? [];
    expect(key).toBe((await call(h, ada, "GET", "/api/push")).body.key);
    const [head, claims, signature] = token.split(".");
    const verified = await crypto.subtle.verify(
      { name: "ECDSA", hash: "SHA-256" },
      await crypto.subtle.importKey(
        "raw",
        fromBase64url(key),
        { name: "ECDSA", namedCurve: "P-256" },
        false,
        ["verify"],
      ),
      fromBase64url(signature),
      new TextEncoder().encode(`${head}.${claims}`),
    );
    expect(verified).toBe(true);
    expect(
      JSON.parse(new TextDecoder().decode(fromBase64url(claims))),
    ).toMatchObject({
      aud: `https://${PUSH_HOST}`,
      sub: SUBJECT,
    });
    expect(push.bytes).toBeGreaterThan(100);
  });

  it("sends to every browser of the learner and to nobody without one", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await subscribe(h, ada, "/phone");
    await subscribe(h, ada, "/laptop");
    await earn(h, ada, "UTC");
    await earn(h, bea, "UTC");
    await h.advance(DAY);

    await h.remind(new Date("2026-10-21T19:17:00Z"));

    expect(
      h.pushes.map((p) => new URL(p.endpoint).pathname).toSorted(),
    ).toEqual(["/laptop", "/phone"]);
  });

  it("skips a learner whose streak already ended", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    await subscribe(h, ada, "/ada");
    await earn(h, ada, "UTC");
    // Tuesday's XP, then Wednesday and Thursday with none: the streak is gone.
    await h.advance(2 * DAY);

    await h.remind(new Date("2026-10-22T19:17:00Z"));

    expect(h.pushes).toEqual([]);
  });

  it("forgets a browser the push service no longer knows", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    await subscribe(h, ada, "/gone/ada");
    await subscribe(h, ada, "/alive");
    await earn(h, ada, "UTC");
    await h.advance(DAY);

    await h.remind(new Date("2026-10-21T19:17:00Z"));
    const rows = await h.db
      .prepare("SELECT endpoint FROM push_subscriptions")
      .all<{ endpoint: string }>();

    expect(rows.results.map((row) => new URL(row.endpoint).pathname)).toEqual([
      "/alive",
    ]);
  });
});

describe("/api/push", () => {
  it("serves the public key and the hour of the reminder", async () => {
    const h = await worker();
    const ada = await user(h, "ada");

    const reply = await call(h, ada, "GET", "/api/push");

    expect(reply.status).toBe(200);
    // An uncompressed P-256 point: 65 bytes, 87 characters of base64url.
    expect(reply.body.key).toMatch(/^B[A-Za-z0-9_-]{86}$/);
    expect(reply.body.hour).toBe(19);
  });

  it("answers 503 on a deployment without VAPID secrets", async () => {
    const h = await worker({ VAPID_PUBLIC_KEY: "" });
    const ada = await user(h, "ada");

    expect((await call(h, ada, "GET", "/api/push")).body.reason).toBe(
      "push_unavailable",
    );
  });

  it("refuses an endpoint outside the push services", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const sub = await browser("/x");

    for (const endpoint of [
      "http://push.example.test/x",
      "https://evil.test/x",
      "https://push.example.test.evil.test/x",
      "not a url",
    ]) {
      const reply = await call(h, ada, "POST", "/api/push", {
        ...sub,
        endpoint,
      });
      expect(reply.status, endpoint).toBe(400);
    }
  });

  it("holds five browsers per learner and deletes one on request", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    for (let k = 0; k < 5; k++) await subscribe(h, ada, `/b${k}`);

    const sixth = await call(h, ada, "POST", "/api/push", await browser("/b5"));
    expect(sixth.status).toBe(429);
    // The same browser again is not a sixth.
    await subscribe(h, ada, "/b0");
    const gone = await call(h, ada, "DELETE", "/api/push", {
      endpoint: `https://${PUSH_HOST}/b0`,
    });
    expect(gone.status).toBe(204);
    expect((await subscribe(h, ada, "/b5")).endsWith("/b5")).toBe(true);
  });

  it("moves a browser to the account that registers it and lets only that account delete it", async () => {
    const h = await worker();
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const endpoint = await subscribe(h, ada, "/shared");
    await subscribe(h, bea, "/shared");
    const count = async () =>
      await h.db
        .prepare("SELECT COUNT(*) AS n FROM push_subscriptions")
        .first<number>("n");

    // The browser belongs to Bea now, so Ada's delete changes nothing.
    await call(h, ada, "DELETE", "/api/push", { endpoint });
    expect(await count()).toBe(1);
    await call(h, bea, "DELETE", "/api/push", { endpoint });
    expect(await count()).toBe(0);
  });
});

describe("GET /api/xp", () => {
  it("counts today in the learner's own day, apart from the UTC day", async () => {
    const h = await worker({ FAKE_CLOCK: "2026-10-21T04:00:00Z" });
    const ada = await user(h, "ada");
    // 04:00 UTC is 21:00 on the 20th in Los Angeles.
    await earn(h, ada, "America/Los_Angeles");
    await h.advance(5 * HOUR);

    const now = (await call(h, ada, "GET", "/api/xp")).body;

    // 09:00 UTC is 02:00 on the 21st in Los Angeles: a new day with no XP,
    // while the UTC day still holds the five.
    expect(now).toEqual({ total: 5, cap: 300, today: 0 });
  });
});
