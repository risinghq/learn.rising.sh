import { afterEach, describe, expect, it } from "vitest";

import {
  type Harness,
  type Options,
  TOKEN,
  clearOfMinuteEnd,
  start as startWorker,
} from "./harness.ts";
import { signIn } from "./signin.ts";

const open: Harness[] = [];

async function worker(options?: Options): Promise<Harness> {
  const h = await startWorker(options);
  open.push(h);
  return h;
}

afterEach(async () => {
  await Promise.all(open.splice(0).map((h) => h.dispose()));
});

const origin = { origin: "http://runner.test" };
const HOUR = 3_600_000;
const DAY = 24 * HOUR;
// The fixture starts on a Wednesday.
const CLOCK = "2026-10-21T12:00:00Z";
// Long enough to avoid accidental matches in replies.
const subjectOf = (name: string) => `subject-${name}-8c1f2d9a`;

interface Who {
  name: string;
  cookie: string;
}

async function user(h: Harness, name: string): Promise<Who> {
  const { cookie } = await signIn(h, "google", subjectOf(name));
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
    headers: { ...origin, cookie: who.cookie },
    body,
  });

const xp = (
  h: Harness,
  who: Who,
  source: string,
  ref: string,
  amount: number,
  extra: Record<string, unknown> = {},
) => call(h, who, "POST", "/api/xp", { source, ref, amount, ...extra });

const streak = async (h: Harness, who: Who) =>
  (await call(h, who, "GET", "/api/streak")).body;

const check = (h: Harness, who: Who, exercise: string, code: string) =>
  h.post(
    { code, mode: "check", exercise },
    { headers: { cookie: who.cookie, "x-turnstile-token": TOKEN } },
  );

async function befriend(h: Harness, a: Who, b: Who): Promise<void> {
  const invite = await call(h, a, "POST", "/api/friends/invite");
  const accepted = await call(h, b, "POST", "/api/friends/accept", {
    code: invite.body.code,
  });
  expect(accepted.status).toBe(200);
}

// Earns one XP on each consecutive day and leaves the clock on the last.
// `quitAfter` stops selected users early.
async function earnDays(
  h: Harness,
  users: Who[],
  days: number,
  quitAfter: Record<string, number> = {},
): Promise<void> {
  for (let day = 0; day < days; day++) {
    if (day > 0) await h.advance(DAY);
    for (const who of users) {
      if (day >= (quitAfter[who.name] ?? days)) continue;
      expect((await xp(h, who, "drill", "d1", 1)).body.granted).toBe(1);
    }
  }
}

describe("POST /api/xp", () => {
  it("caps the XP of a UTC day across all sources and grants what fits", async () => {
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, XP_PER_DAY: "120" },
    });
    const ada = await user(h, "ada");

    const first = await xp(h, ada, "drill", "a", 50);
    expect(first.status).toBe(200);
    expect(first.body).toEqual({
      granted: 50,
      total: 50,
      cap: 120,
      reason: null,
    });
    expect((await xp(h, ada, "cli", "b", 50)).body.granted).toBe(50);
    const partial = await xp(h, ada, "lesson", "intro", 50);
    expect(partial.body).toEqual({
      granted: 20,
      total: 120,
      cap: 120,
      reason: null,
    });
    const refused = await xp(h, ada, "drill", "c", 5);
    expect(refused.status).toBe(200);
    expect(refused.body).toEqual({
      granted: 0,
      total: 120,
      cap: 120,
      reason: "daily_cap",
    });
    const rows = await h.db
      .prepare("SELECT COUNT(*) AS n, SUM(amount) AS sum FROM xp_events")
      .first<{ n: number; sum: number }>();
    expect(rows).toEqual({ n: 3, sum: 120 });

    const bea = await user(h, "bea");
    expect((await xp(h, bea, "drill", "a", 50)).body.granted).toBe(50);

    await h.advance(12 * HOUR);
    expect((await xp(h, ada, "drill", "c", 5)).body.granted).toBe(5);
  });

  it("awards a ref once per UTC day for each source", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");

    expect((await xp(h, ada, "drill", "q1", 10)).body.granted).toBe(10);
    const again = await xp(h, ada, "drill", "q1", 10);
    expect(again.body).toEqual({
      granted: 0,
      total: 10,
      cap: 300,
      reason: "ref_today",
    });
    expect((await xp(h, ada, "drill", "q1", 40)).body.granted).toBe(0);
    expect((await xp(h, ada, "cli", "q1", 10)).body.granted).toBe(10);
    expect(
      (await h.db.prepare("SELECT COUNT(*) AS n FROM xp_events").first<{
        n: number;
      }>())!.n,
    ).toBe(2);

    await h.advance(DAY);
    expect((await xp(h, ada, "drill", "q1", 10)).body.granted).toBe(10);
  });

  it("keeps the day an award was earned, so a resend after midnight is not a second award", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const earnedAt = Date.parse(CLOCK);
    const post = { earnedAt, tz: "UTC" };

    expect((await xp(h, ada, "drill", "q1", 10, post)).body.granted).toBe(10);
    const before = (await call(h, ada, "GET", "/api/board")).body.entries;

    // The reply was lost and the queue resends after UTC midnight.
    await h.advance(13 * HOUR);
    const again = await xp(h, ada, "drill", "q1", 10, post);
    expect(again.body.granted).toBe(0);
    expect(again.body.reason).toBe("ref_today");
    expect((await call(h, ada, "GET", "/api/board")).body.entries).toEqual(
      before,
    );
    expect(
      (await h.db.prepare("SELECT COUNT(*) AS n FROM xp_events").first<{
        n: number;
      }>())!.n,
    ).toBe(1);
    // The streak counted the day of the award once.
    expect((await streak(h, ada)).current).toBe(1);
  });

  it("dates an award by earnedAt only inside the last 48 hours", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const now = Date.parse(CLOCK);
    const rows = () =>
      h.db
        .prepare("SELECT ref, at, utc_day FROM xp_events ORDER BY ref")
        .all<{ ref: string; at: number; utc_day: number }>();

    await xp(h, ada, "drill", "recent", 5, { earnedAt: now - DAY });
    await xp(h, ada, "drill", "ancient", 5, { earnedAt: now - 10 * DAY });
    await xp(h, ada, "drill", "future", 5, { earnedAt: now + DAY });
    await xp(h, ada, "drill", "absent", 5);

    const day = Math.floor(now / DAY);
    expect((await rows()).results).toEqual([
      { ref: "absent", at: now / 1000, utc_day: day },
      { ref: "ancient", at: now / 1000, utc_day: day },
      { ref: "future", at: now / 1000, utc_day: day },
      { ref: "recent", at: (now - DAY) / 1000, utc_day: day - 1 },
    ]);
    expect(
      (await xp(h, ada, "drill", "bad", 5, { earnedAt: "yesterday" })).status,
    ).toBe(400);
  });

  it("refuses exercise XP until the server recorded a passing check for this user", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const refused = (who: Who) => xp(h, who, "exercise", "intro/uno", 20);

    expect((await refused(ada)).status).toBe(403);
    expect((await refused(ada)).body.reason).toBe("not_passed");

    // The page claiming a pass is not a record.
    await call(h, ada, "PUT", "/api/progress", {
      exercises: {
        "intro/uno": { code: "x", hints: 0, checks: 1, passed: true, at: 10 },
      },
    });
    // Neither is a failing check, nor a run.
    await check(h, ada, "intro/uno", "FALLA");
    await h.post(
      { code: "print(1)", mode: "run", exercise: "intro/uno" },
      { headers: { cookie: ada.cookie, "x-turnstile-token": TOKEN } },
    );
    expect((await refused(ada)).status).toBe(403);

    // Another user's pass is not Ada's.
    await check(h, bea, "intro/uno", "print(1)");
    expect((await refused(ada)).status).toBe(403);
    // A pass of Ada's in another exercise is not this one's.
    await check(h, ada, "intro/dos", "print(1)");
    expect((await refused(ada)).status).toBe(403);

    await check(h, ada, "intro/uno", "print(1)");
    expect((await refused(ada)).body.granted).toBe(20);
    expect((await refused(bea)).body.granted).toBe(20);
    expect(
      (await h.db.prepare("SELECT COUNT(*) AS n FROM xp_events").first<{
        n: number;
      }>())!.n,
    ).toBe(2);
  });

  it.each([
    ["an unknown source", { source: "video", ref: "a", amount: 1 }],
    ["no source", { ref: "a", amount: 1 }],
    [
      "an exercise ref that is not lesson/exercise",
      { source: "exercise", ref: "uno", amount: 1 },
    ],
    ["a lesson ref with a slash", { source: "lesson", ref: "a/b", amount: 1 }],
    ["an empty ref", { source: "drill", ref: "", amount: 1 }],
    ["a long ref", { source: "drill", ref: "a".repeat(101), amount: 1 }],
    ["a zero amount", { source: "drill", ref: "a", amount: 0 }],
    ["a negative amount", { source: "drill", ref: "a", amount: -5 }],
    ["a fractional amount", { source: "drill", ref: "a", amount: 1.5 }],
    ["a text amount", { source: "drill", ref: "a", amount: "5" }],
    [
      "an amount over the per-event cap",
      { source: "drill", ref: "a", amount: 51 },
    ],
    ["an unknown field", { source: "drill", ref: "a", amount: 1, bonus: 9 }],
    [
      "a time zone that does not exist",
      { source: "drill", ref: "a", amount: 1, tz: "Mars/Olympus" },
    ],
    ["a body that is not an object", [1, 2]],
  ])("rejects %s with 400 and stores nothing", async (_name, body) => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const reply = await call(h, ada, "POST", "/api/xp", body);
    expect(reply.status).toBe(400);
    expect(reply.body.reason).toBe("bad_request");
    expect(
      (await h.db.prepare("SELECT COUNT(*) AS n FROM xp_events").first<{
        n: number;
      }>())!.n,
    ).toBe(0);
  });

  it("answers 401 without a session and 403 from another origin", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const body = { source: "drill", ref: "a", amount: 1 };
    const anonymous = await h.request("POST", "/api/xp", {
      headers: origin,
      body,
    });
    expect(anonymous.status).toBe(401);
    const foreign = await h.request("POST", "/api/xp", {
      headers: { origin: "http://evil.test", cookie: ada.cookie },
      body,
    });
    expect(foreign.status).toBe(403);
    for (const route of ["/api/streak", "/api/friends", "/api/board"]) {
      expect((await h.request("GET", route)).status, route).toBe(401);
    }
  });

  it("counts the XP route against the per-user limit", async () => {
    // The limiter's alarm deletes its counter at once under a clock in the
    // past, so this test runs on the real one.
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "3" } });
    const ada = await user(h, "ada");
    const statuses: number[] = [];
    for (let i = 0; i < 4; i++) {
      statuses.push((await xp(h, ada, "drill", `r${i}`, 1)).status);
    }
    expect(statuses).toEqual([200, 200, 200, 429]);
  });
});

describe("GET /api/streak", () => {
  it("is zero before any XP", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    expect(await streak(h, ada)).toEqual({
      current: 0,
      longest: 0,
      today: false,
    });
  });

  it("counts consecutive days, keeps yesterday's streak alive and then drops it", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    await earnDays(h, [ada], 3);
    expect(await streak(h, ada)).toEqual({
      current: 3,
      longest: 3,
      today: true,
    });
    // Tomorrow has not been earned yet: the streak still stands.
    await h.advance(DAY);
    expect(await streak(h, ada)).toEqual({
      current: 3,
      longest: 3,
      today: false,
    });
    // A day was missed and there is no freeze.
    await h.advance(DAY);
    expect(await streak(h, ada)).toEqual({
      current: 0,
      longest: 3,
      today: false,
    });
    await xp(h, ada, "drill", "d1", 1);
    expect(await streak(h, ada)).toEqual({
      current: 1,
      longest: 3,
      today: true,
    });
  });

  it("splits days at the learner's midnight, not at UTC's", async () => {
    // 06:30 UTC is 23:30 on the 20th in Los Angeles (UTC-7); 07:30 UTC is 00:30 on the 21st.
    const vars = { FAKE_CLOCK: "2026-10-21T06:30:00Z" };
    const h = await worker({ vars });
    const west = await user(h, "west");
    const utc = await user(h, "utc");

    await xp(h, west, "drill", "a", 5, { tz: "America/Los_Angeles" });
    await xp(h, utc, "drill", "a", 5);
    await h.advance(HOUR);
    await xp(h, west, "drill", "b", 5);
    await xp(h, utc, "drill", "b", 5);

    expect(await streak(h, west)).toEqual({
      current: 2,
      longest: 2,
      today: true,
    });
    // The same two events fall on one UTC day.
    expect(await streak(h, utc)).toEqual({
      current: 1,
      longest: 1,
      today: true,
    });
    // The zone is stored on the user: a later request without `tz` keeps it.
    const zone = await h.db
      .prepare("SELECT time_zone FROM users ORDER BY time_zone")
      .all<{ time_zone: string }>();
    expect(zone.results.map((row) => row.time_zone)).toEqual([
      "America/Los_Angeles",
      "UTC",
    ]);
  });

  it("covers a missed day with a freeze earned at 7 streak days", async () => {
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, AUTH_SESSION_DAYS: "90" },
    });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    // Bea stops one day short of a freeze.
    await earnDays(h, [ada, bea], 7, { bea: 6 });
    expect(await streak(h, ada)).toEqual({
      current: 7,
      longest: 7,
      today: true,
    });

    // One day passes with nothing earned: Bea has no freeze, Ada has one.
    await h.advance(DAY);
    expect(await streak(h, ada)).toEqual({
      current: 7,
      longest: 7,
      today: false,
    });
    expect(await streak(h, bea)).toEqual({
      current: 0,
      longest: 6,
      today: false,
    });

    // Ada earns after a missed day: the freeze took it, so the streak goes on.
    await h.advance(DAY);
    await xp(h, ada, "drill", "d1", 1);
    await xp(h, bea, "drill", "d1", 1);
    expect(await streak(h, ada)).toEqual({
      current: 8,
      longest: 8,
      today: true,
    });
    expect(await streak(h, bea)).toEqual({
      current: 1,
      longest: 6,
      today: true,
    });

    // The freeze was spent: another miss breaks Ada's streak.
    await h.advance(2 * DAY);
    await xp(h, ada, "drill", "d1", 1);
    expect(await streak(h, ada)).toEqual({
      current: 1,
      longest: 8,
      today: true,
    });
  });

  // 21 days earn three freezes, and only two are kept.
  it.each([
    ["covers two missed days", 2, { current: 22, longest: 22 }],
    ["breaks on three", 3, { current: 1, longest: 21 }],
  ])("holds at most 2 freezes: %s", async (_name, missed, expected) => {
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, AUTH_SESSION_DAYS: "90" },
    });
    const ada = await user(h, "ada");
    await earnDays(h, [ada], 21);
    await h.advance((missed + 1) * DAY);
    await xp(h, ada, "drill", "d1", 1);
    expect(await streak(h, ada)).toEqual({ ...expected, today: true });
  });

  it("keeps the streak after the purge deletes the old XP rows", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    await earnDays(h, [ada], 3);
    await h.purge(new Date(Date.parse(CLOCK) + 30 * DAY));
    const rows = await h.db
      .prepare("SELECT COUNT(*) AS n FROM xp_events")
      .first<{ n: number }>();
    expect(rows!.n).toBe(0);
    expect(await streak(h, ada)).toEqual({
      current: 3,
      longest: 3,
      today: true,
    });
  });
});

describe("friends", () => {
  it("makes a friendship mutual with a single-use code and lists no identity", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await xp(h, ada, "drill", "a", 7);
    await xp(h, bea, "drill", "a", 11);
    await h.advance(DAY);
    await xp(h, bea, "drill", "a", 11);

    const invite = await call(h, ada, "POST", "/api/friends/invite");
    expect(invite.status).toBe(200);
    expect(invite.body.code).toMatch(/^[A-Z2-9]{5}-[A-Z2-9]{5}$/);
    const now = Date.parse(CLOCK) + DAY;
    expect(invite.body.expiresAt).toBe(now + 7 * DAY);
    // The database keeps a hash, never the code.
    const stored = await h.db
      .prepare("SELECT code_hash FROM friend_invites")
      .all<{ code_hash: string }>();
    expect(stored.results).toHaveLength(1);
    expect(JSON.stringify(stored.results)).not.toContain(
      invite.body.code.replace("-", ""),
    );

    const accepted = await call(h, bea, "POST", "/api/friends/accept", {
      code: invite.body.code.toLowerCase().replace("-", " "),
    });
    expect(accepted.status).toBe(200);

    const adaList = await call(h, ada, "GET", "/api/friends");
    const beaList = await call(h, bea, "GET", "/api/friends");
    expect(adaList.body.friends).toHaveLength(1);
    expect(beaList.body.friends).toHaveLength(1);
    // Ada sees Bea's streak and week, and Bea Ada's.
    expect(adaList.body.friends[0]).toMatchObject({
      streak: 2,
      today: true,
      xp: 22,
    });
    expect(beaList.body.friends[0]).toMatchObject({
      streak: 1,
      today: false,
      xp: 7,
    });
    // An id, the streak, today and the XP: nothing that names a person.
    expect(Object.keys(adaList.body.friends[0]).toSorted()).toEqual([
      "id",
      "streak",
      "today",
      "xp",
    ]);
    const everything = JSON.stringify([adaList.body, beaList.body]);
    const ids = await h.db
      .prepare("SELECT id FROM users")
      .all<{ id: string }>();
    for (const secret of [
      subjectOf("ada"),
      subjectOf("bea"),
      "google",
      ...ids.results.map((row) => row.id),
    ]) {
      expect(everything).not.toContain(secret);
    }
  });

  it("rejects an expired code, a reused one and the ones that were never issued", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const cy = await user(h, "cy");
    const accept = (who: Who, code: string) =>
      call(h, who, "POST", "/api/friends/accept", { code });

    const stale = await call(h, ada, "POST", "/api/friends/invite");
    await h.advance(7 * DAY - 1000);
    // A code issued a second before the first expires is still live after it.
    const live = await call(h, ada, "POST", "/api/friends/invite");
    await h.advance(1000);
    const expired = await accept(bea, stale.body.code);
    expect(expired.status).toBe(410);
    expect(expired.body.reason).toBe("invite_expired");
    expect((await call(h, bea, "GET", "/api/friends")).body.friends).toEqual(
      [],
    );

    expect((await accept(bea, live.body.code)).status).toBe(200);
    const reused = await accept(cy, live.body.code);
    expect(reused.status).toBe(410);
    expect(reused.body.reason).toBe("invite_used");
    expect((await call(h, cy, "GET", "/api/friends")).body.friends).toEqual([]);

    const unknown = await accept(cy, "AAAAA-AAAAA");
    expect(unknown.status).toBe(404);
    expect(unknown.body.reason).toBe("invite_unknown");
    expect((await accept(cy, "")).status).toBe(400);
  });

  it("does not let a user accept their own code or befriend twice, and a refusal leaves the code unspent", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const accept = (who: Who, code: string) =>
      call(h, who, "POST", "/api/friends/accept", { code });

    const first = await call(h, ada, "POST", "/api/friends/invite");
    const own = await accept(ada, first.body.code);
    expect(own.status).toBe(400);
    expect(own.body.reason).toBe("own_code");
    expect((await accept(bea, first.body.code)).status).toBe(200);

    const second = await call(h, ada, "POST", "/api/friends/invite");
    const twice = await accept(bea, second.body.code);
    expect(twice.status).toBe(409);
    expect(twice.body.reason).toBe("already_friends");
    const unspent = await h.db
      .prepare("SELECT COUNT(*) AS n FROM friend_invites WHERE used_at IS NULL")
      .first<{ n: number }>();
    expect(unspent!.n).toBe(1);
  });

  it("limits friends per account and open invites per user", async () => {
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, MAX_FRIENDS: "1" },
    });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const cy = await user(h, "cy");
    await befriend(h, ada, bea);
    const invite = await call(h, cy, "POST", "/api/friends/invite");
    const full = await call(h, ada, "POST", "/api/friends/accept", {
      code: invite.body.code,
    });
    expect(full.status).toBe(409);
    expect(full.body.reason).toBe("friend_limit");

    const codes: number[] = [];
    for (let i = 0; i < 6; i++) {
      codes.push((await call(h, cy, "POST", "/api/friends/invite")).status);
    }
    // `invite` above is the first open one.
    expect(codes).toEqual([200, 200, 200, 200, 429, 429]);
  });

  it("holds the friend limit and the pair when accepts race", async () => {
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, MAX_FRIENDS: "1" },
    });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const cy = await user(h, "cy");
    const accept = (who: Who, code: string) =>
      call(h, who, "POST", "/api/friends/accept", { code });
    const invite = async (who: Who) =>
      (await call(h, who, "POST", "/api/friends/invite")).body.code;

    // Ada has one slot left: only one of two simultaneous accepts gets it.
    const [fromBea, fromCy] = [await invite(bea), await invite(cy)];
    const raced = await Promise.all([
      accept(ada, fromBea),
      accept(ada, fromCy),
    ]);
    expect(raced.map((r) => r.status).toSorted()).toEqual([200, 409]);

    // Two codes of one person accepted at once make one friendship, not a 500.
    const h2 = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const dan = await user(h2, "dan");
    const eve = await user(h2, "eve");
    const codes = [
      await call(h2, dan, "POST", "/api/friends/invite"),
      await call(h2, dan, "POST", "/api/friends/invite"),
    ].map((r) => r.body.code);
    const pair = await Promise.all(
      codes.map((code) =>
        call(h2, eve, "POST", "/api/friends/accept", { code }),
      ),
    );
    expect(pair.map((r) => r.status).toSorted()).toEqual([200, 409]);
    const rows = await h2.db
      .prepare("SELECT COUNT(*) AS n FROM friendships")
      .first<{ n: number }>();
    expect(rows!.n).toBe(2);
  });

  it("removes a friendship for both sides and only for its owner", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const cy = await user(h, "cy");
    await befriend(h, ada, bea);
    const [theirs] = (await call(h, ada, "GET", "/api/friends")).body.friends;

    // Cy cannot remove it, nor guess it.
    expect(
      (await call(h, cy, "DELETE", `/api/friends/${theirs.id}`)).status,
    ).toBe(404);
    expect((await call(h, ada, "DELETE", "/api/friends/abc")).status).toBe(404);
    expect(
      (await call(h, ada, "GET", "/api/friends")).body.friends,
    ).toHaveLength(1);

    expect(
      (await call(h, ada, "DELETE", `/api/friends/${theirs.id}`)).status,
    ).toBe(204);
    expect((await call(h, ada, "GET", "/api/friends")).body.friends).toEqual(
      [],
    );
    expect((await call(h, bea, "GET", "/api/friends")).body.friends).toEqual(
      [],
    );
    expect(
      (await call(h, ada, "DELETE", `/api/friends/${theirs.id}`)).status,
    ).toBe(404);
  });

  it("deletes the friendships and invites of a deleted account", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    await befriend(h, ada, bea);
    await xp(h, ada, "drill", "a", 5);
    await call(h, ada, "POST", "/api/friends/invite");
    await call(h, ada, "DELETE", "/api/me");
    for (const table of ["friendships", "friend_invites", "xp_events"]) {
      const row = await h.db
        .prepare(`SELECT COUNT(*) AS n FROM ${table}`)
        .first<{ n: number }>();
      expect(row!.n, table).toBe(0);
    }
    expect((await call(h, bea, "GET", "/api/friends")).body.friends).toEqual(
      [],
    );
  });
});

describe("GET /api/board", () => {
  const entries = (body: any) =>
    body.entries.map((entry: any) => [entry.you, entry.rank, entry.xp]);

  it("ranks the user and friends by XP this week, ties sharing a rank", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const bea = await user(h, "bea");
    const cy = await user(h, "cy");
    const stranger = await user(h, "stranger");
    await befriend(h, ada, bea);
    await befriend(h, ada, cy);
    await xp(h, ada, "drill", "a", 20);
    await xp(h, bea, "drill", "a", 40);
    await xp(h, cy, "drill", "a", 20);
    await xp(h, stranger, "drill", "a", 50);

    const board = await call(h, ada, "GET", "/api/board");
    expect(board.status).toBe(200);
    // Wednesday 21 October: the week began on Monday the 19th.
    expect(board.body.weekStart).toBe("2026-10-19");
    expect(entries(board.body)).toEqual([
      [false, 1, 40],
      [true, 2, 20],
      [false, 2, 20],
    ]);
    // Friends do not see strangers, and Bea sees only Ada.
    expect(entries((await call(h, bea, "GET", "/api/board")).body)).toEqual([
      [true, 1, 40],
      [false, 2, 20],
    ]);
    // A friend's entry carries the id of the friendship from /api/friends.
    const friends = (await call(h, ada, "GET", "/api/friends")).body.friends;
    expect(
      board.body.entries
        .filter((e: any) => !e.you)
        .map((e: any) => e.id)
        .toSorted(),
    ).toEqual(friends.map((f: any) => f.id).toSorted());
    expect(board.body.entries.find((e: any) => e.you).id).toBeNull();
  });

  it("starts the week on Monday 00:00 in the user's zone", async () => {
    // Sunday 25 October, 23:30 UTC.
    const h = await worker({ vars: { FAKE_CLOCK: "2026-10-25T23:30:00Z" } });
    const utc = await user(h, "utc");
    const west = await user(h, "west");
    await befriend(h, utc, west);
    await xp(h, utc, "drill", "a", 30);
    await xp(h, west, "drill", "a", 20, { tz: "America/Los_Angeles" });

    expect((await call(h, utc, "GET", "/api/board")).body.weekStart).toBe(
      "2026-10-19",
    );
    expect(entries((await call(h, utc, "GET", "/api/board")).body)).toEqual([
      [true, 1, 30],
      [false, 2, 20],
    ]);

    // Monday 00:30 UTC: a new week for UTC, still Sunday evening in Los Angeles.
    await h.advance(HOUR);
    await xp(h, utc, "drill", "b", 5);
    await xp(h, west, "drill", "b", 10);
    const utcBoard = await call(h, utc, "GET", "/api/board");
    expect(utcBoard.body.weekStart).toBe("2026-10-26");
    expect(entries(utcBoard.body)).toEqual([
      [false, 1, 10],
      [true, 2, 5],
    ]);
    const westBoard = await call(h, west, "GET", "/api/board");
    expect(westBoard.body.weekStart).toBe("2026-10-19");
    // Sunday evening in Los Angeles: the 30 and 5 of UTC are all this week's.
    expect(entries(westBoard.body)).toEqual([
      [false, 1, 35],
      [true, 2, 30],
    ]);

    // Monday 07:00 UTC is Monday 00:00 in Los Angeles.
    await h.advance(6.5 * HOUR);
    await xp(h, west, "drill", "c", 1);
    const later = await call(h, west, "GET", "/api/board");
    expect(later.body.weekStart).toBe("2026-10-26");
    expect(entries(later.body)).toEqual([
      [true, 1, 1],
      [false, 2, 0],
    ]);
  });

  it("lists the user alone when there are no friends", async () => {
    const h = await worker({ vars: { FAKE_CLOCK: CLOCK } });
    const ada = await user(h, "ada");
    const board = await call(h, ada, "GET", "/api/board");
    expect(entries(board.body)).toEqual([[true, 1, 0]]);
  });
});
