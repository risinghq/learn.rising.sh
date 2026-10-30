import { describe, expect, test } from "vitest";

import { type Item, itemSchema } from "./item.ts";
import { MAX_SESSION, type Review, planSession } from "./schedule.ts";

const DAY = 86_400_000;
const T0 = Date.UTC(2026, 0, 1, 9);

const choice = (lesson: string, name: string): Item =>
  itemSchema.parse({
    id: `${lesson}:${name}`,
    lesson,
    prompt: name,
    kind: "choice",
    options: ["a", "b"],
    right: 0,
  });

const bet = (lesson: string, name: string): Item =>
  itemSchema.parse({
    id: `${lesson}:${name}`,
    lesson,
    prompt: name,
    kind: "predict",
    options: ["a", "b"],
    after: "Anotado.",
  });

const answer = (item: Item, daysAgo: number, correct: boolean): Review => ({
  item: item.id,
  at: T0 - daysAgo * DAY,
  correct,
});

const ids = (items: Item[]): string[] => items.map((item) => item.id);

describe("planSession", () => {
  test("a missed item comes back before a known one", async () => {
    const known = choice("l1", "known");
    const missed = choice("l1", "missed");
    const log = [answer(known, 30, true), answer(missed, 30, false)];
    const session = await planSession({
      bank: [known, missed],
      log,
      done: ["l1"],
      now: T0,
    });
    expect(ids(session)).toEqual(["l1:missed", "l1:known"]);
  });

  test("a missed item is due the next day and a known one after three", async () => {
    const known = choice("l1", "known");
    const missed = choice("l1", "missed");
    const bank = [known, missed];
    const log = [answer(known, 2, true), answer(missed, 2, false)];
    const at = (days: number) =>
      planSession({ bank, log, done: ["l1"], now: T0 - 2 * DAY + days * DAY });
    expect(ids(await at(0.5))).toEqual([]);
    expect(ids(await at(1))).toEqual(["l1:missed"]);
    expect(ids(await at(2.9))).toEqual(["l1:missed"]);
    expect(ids(await at(3))).toEqual(["l1:missed", "l1:known"]);
  });

  test("a miss after right answers brings the item back while a steady one waits", async () => {
    const steady = choice("l1", "steady");
    const slipped = choice("l1", "slipped");
    const log = [
      answer(steady, 20, true),
      answer(steady, 15, true),
      answer(steady, 3, true),
      answer(slipped, 20, true),
      answer(slipped, 15, true),
      answer(slipped, 3, false),
    ];
    const session = await planSession({
      bank: [steady, slipped],
      log,
      done: ["l1"],
      now: T0,
    });
    expect(ids(session)).toEqual(["l1:slipped"]);
  });

  test("the answers can come in any order", async () => {
    const item = choice("l1", "a");
    const log = [
      answer(item, 5, true),
      answer(item, 4, false),
      answer(item, 1, true),
    ];
    const bank = [item];
    const first = await planSession({ bank, log, done: ["l1"], now: T0 });
    const second = await planSession({
      bank,
      log: log.toReversed(),
      done: ["l1"],
      now: T0,
    });
    expect(ids(second)).toEqual(ids(first));
  });

  test("reviews come before new items", async () => {
    const fresh = choice("l1", "fresh");
    const old = choice("l1", "old");
    const session = await planSession({
      bank: [fresh, old],
      log: [answer(old, 30, true)],
      done: ["l1"],
      now: T0,
    });
    expect(ids(session)).toEqual(["l1:old", "l1:fresh"]);
  });

  test("an item that is not due yet stays out", async () => {
    const item = choice("l1", "a");
    const session = await planSession({
      bank: [item],
      log: [answer(item, 0, true)],
      done: ["l1"],
      now: T0,
    });
    expect(session).toEqual([]);
  });

  test("no item of an unfinished lesson, new or due", async () => {
    const open = choice("l1", "open");
    const shut = choice("l2", "shut");
    const old = choice("l2", "old");
    const session = await planSession({
      bank: [open, shut, old],
      log: [answer(old, 30, false)],
      done: ["l1"],
      now: T0,
    });
    expect(ids(session)).toEqual(["l1:open"]);
  });

  test("nothing is chosen before any lesson is finished", async () => {
    const session = await planSession({
      bank: [choice("l1", "a")],
      log: [],
      done: [],
      now: T0,
    });
    expect(session).toEqual([]);
  });

  test("a session has at most 15 items, however many are due or new", async () => {
    const bank = Array.from({ length: 40 }, (_, i) => choice("l1", `q${i}`));
    const fresh = await planSession({ bank, log: [], done: ["l1"], now: T0 });
    expect(fresh).toHaveLength(MAX_SESSION);

    const log = bank.map((item) => answer(item, 30, false));
    const due = await planSession({
      bank,
      log,
      done: ["l1"],
      now: T0,
      size: 100,
    });
    expect(due).toHaveLength(MAX_SESSION);
  });

  test("a smaller size is honoured", async () => {
    const bank = Array.from({ length: 40 }, (_, i) => choice("l1", `q${i}`));
    const session = await planSession({
      bank,
      log: [],
      done: ["l1"],
      now: T0,
      size: 10,
    });
    expect(session).toHaveLength(10);
  });

  test("new items alternate between the finished lessons", async () => {
    const bank = [
      ...["a1", "a2", "a3"].map((name) => choice("la", name)),
      ...["b1", "b2"].map((name) => choice("lb", name)),
    ];
    const session = await planSession({
      bank,
      log: [],
      done: ["la", "lb"],
      now: T0,
      size: 4,
    });
    expect(ids(session)).toEqual(["la:a1", "lb:b1", "la:a2", "lb:b2"]);
  });

  test("a prediction is asked once and never reviewed", async () => {
    const seen = bet("l1", "seen");
    const unseen = bet("l1", "unseen");
    const session = await planSession({
      bank: [seen, unseen],
      log: [answer(seen, 365, true)],
      done: ["l1"],
      now: T0,
    });
    expect(ids(session)).toEqual(["l1:unseen"]);
  });

  test("the same inputs give the same session", async () => {
    const bank = Array.from({ length: 30 }, (_, i) =>
      choice(i % 2 ? "la" : "lb", `q${i}`),
    );
    const log = bank
      .slice(0, 12)
      .map((item, i) => answer(item, 10 + i, i % 3 !== 0));
    const input = { bank, log, done: ["la", "lb"], now: T0 };
    expect(ids(await planSession(input))).toEqual(
      ids(await planSession(input)),
    );
  });
});
