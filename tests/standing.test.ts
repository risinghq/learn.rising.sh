// The XP queues of a browser and what the header shows for a signed-in learner: the account's
// numbers plus the queued XP earned today, in the browser's own day.
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  claimAnonymousXp,
  dayOf,
  migratePreferences,
  PREF,
  readXpQueue,
  standing,
  xpQueueKey,
} from "../site/progress.ts";

const NOW = new Date(2026, 5, 15, 12, 0, 0);
const HOUR = 3600_000;

const store = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, value),
  removeItem: (key: string) => void store.delete(key),
});

const signIn = (earned: boolean) => {
  store.set(PREF.account, "ada");
  store.set(
    PREF.tally,
    JSON.stringify({ streak: 4, earned, xp: 10, day: dayOf(NOW) }),
  );
};
const queue = (owner: string | null, ...posts: object[]) =>
  store.set(
    xpQueueKey(owner),
    JSON.stringify(
      posts.map((post, k) =>
        Object.assign({ source: "drill", ref: `r${k}`, amount: 7 }, post),
      ),
    ),
  );

describe("standing", () => {
  beforeEach(() => store.clear());

  it.each([
    ["yesterday", { earnedAt: NOW.getTime() - 24 * HOUR }, 10, 4],
    ["today", { earnedAt: NOW.getTime() - HOUR }, 17, 5],
    ["no date", {}, 10, 4],
  ])("a queued post from %s", (_, post, today, streak) => {
    signIn(false);
    queue("ada", post);
    expect(standing(NOW)).toEqual({ today, streak });
  });

  it("does not count the queue of another account", () => {
    signIn(false);
    queue("bob", { earnedAt: NOW.getTime() });
    expect(standing(NOW)).toEqual({ today: 10, streak: 4 });
  });

  it("does not extend a streak that today already counts", () => {
    signIn(true);
    queue("ada", { earnedAt: NOW.getTime() });
    expect(standing(NOW)).toEqual({ today: 17, streak: 4 });
  });
});

describe("the queues", () => {
  beforeEach(() => store.clear());

  it("moves the anonymous queue to the account that signs in, and nothing else", () => {
    queue(null, { ref: "before", earnedAt: 1 });
    queue("ada", { ref: "kept", earnedAt: 2 });
    queue("bob", { ref: "bobs", earnedAt: 3 });
    claimAnonymousXp("ada");
    expect(readXpQueue("ada").map((post) => post.ref)).toEqual([
      "kept",
      "before",
    ]);
    expect(readXpQueue("bob").map((post) => post.ref)).toEqual(["bobs"]);
    expect(store.has(xpQueueKey(null))).toBe(false);
  });

  it.each([
    ["nobody signed in", {}, ["old"]],
    ["an account is signed in", { [PREF.account]: "ada" }, []],
    ["an account signed in before", { [PREF.xpSeeded]: "1" }, []],
  ])("the queue of an earlier version, when %s", (_, device, anonymous) => {
    for (const [key, value] of Object.entries(device)) store.set(key, value);
    store.set("rising:xpq", JSON.stringify([{ ref: "old", amount: 5 }]));
    migratePreferences();
    expect(store.has("rising:xpq")).toBe(false);
    expect(readXpQueue(null).map((post) => post.ref)).toEqual(anonymous);
  });

  it("dates an undated post at 0 and keeps it as a drill post", () => {
    store.set("rising:xpq", JSON.stringify([{ ref: "old", amount: 5 }]));
    migratePreferences();
    expect(readXpQueue(null)).toEqual([
      { source: "drill", ref: "old", amount: 5, earnedAt: 0 },
    ]);
  });
});
