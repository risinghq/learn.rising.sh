import { describe, expect, it } from "vitest";

import type { Item } from "../../../drill/item.ts";
import { answer, begin, finished, next, turnOf } from "./run.ts";

const item = (id: string): Item => ({
  kind: "choice",
  id: `lesson:${id}`,
  lesson: "lesson",
  prompt: id,
  options: ["a", "b"],
  right: 0,
});

describe("a drill session", () => {
  it("brings a missed item back once at the end and pays less for it", () => {
    let run = begin([item("a"), item("b")]);
    run = next(answer(run, false, 1));
    run = next(answer(run, true, 2));
    expect(run.turns.map((t) => [t.item.id, t.retry])).toEqual([
      ["lesson:a", false],
      ["lesson:b", false],
      ["lesson:a", true],
    ]);
    run = next(answer(run, true, 3));
    expect(finished(run)).toBe(true);
    expect(run.xp).toBe(2 + 1);
    expect(run.first).toBe(1);
  });

  it("logs only the first answer to an item", () => {
    let run = begin([item("a")]);
    run = next(answer(run, false, 10));
    run = next(answer(run, true, 20));
    expect(run.reviews).toEqual([{ item: "lesson:a", at: 10, correct: false }]);
  });

  it("does not ask for a second return after a second miss", () => {
    let run = begin([item("a")]);
    run = next(answer(run, false, 1));
    run = next(answer(run, false, 2));
    expect(finished(run)).toBe(true);
    expect(run.turns).toHaveLength(2);
    expect(run.xp).toBe(0);
    expect(turnOf(run)).toBeUndefined();
  });
});
