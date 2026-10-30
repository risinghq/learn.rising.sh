import { describe, expect, test } from "vitest";

import { type ItemOf, itemSchema } from "./item.ts";
import { parsonsPool } from "./present.ts";

const parsons = (fields: object): ItemOf<"parsons"> =>
  itemSchema.parse({
    id: "l:p",
    lesson: "l",
    prompt: "p",
    kind: "parsons",
    ...fields,
  }) as ItemOf<"parsons">;

describe("parsonsPool", () => {
  const item = parsons({
    lines: ["a = 1", "b = a", "c = b", "d = c", "print(d)"],
    distractors: ["b = 2", "e = 5"],
  });

  test("holds the lines and the distractors, each once", () => {
    expect(parsonsPool(item, "s").toSorted()).toEqual(
      [...item.lines, ...item.distractors].toSorted(),
    );
  });

  test("is the same for the same seed and differs between seeds", () => {
    expect(parsonsPool(item, "s")).toEqual(parsonsPool(item, "s"));
    const orders = new Set(
      Array.from({ length: 20 }, (_, i) =>
        parsonsPool(item, `s${i}`).join("|"),
      ),
    );
    expect(orders.size).toBeGreaterThan(10);
  });

  test("never starts out solved", () => {
    const two = parsons({ lines: ["a = 1", "print(a)"] });
    for (let i = 0; i < 200; i++) {
      expect(parsonsPool(two, `s${i}`)).not.toEqual(two.lines);
      expect(parsonsPool(item, `s${i}`).slice(0, 5)).not.toEqual(item.lines);
    }
  });

  test("can hold repeated lines", () => {
    const repeated = parsons({ lines: ["x += 1", "x *= 2", "x += 1"] });
    expect(parsonsPool(repeated, "s").toSorted()).toEqual([
      "x *= 2",
      "x += 1",
      "x += 1",
    ]);
  });
});
