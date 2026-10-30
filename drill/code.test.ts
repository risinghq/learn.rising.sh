import { describe, expect, test } from "vitest";

import {
  type Outcome,
  type Program,
  type Runner,
  checksOf,
  solution,
  verify,
} from "./code.ts";
import { type Item, itemSchema } from "./item.ts";

const item = (fields: object): Item =>
  itemSchema.parse({ id: "l:x", lesson: "l", prompt: "p", ...fields });

const parsons = item({
  kind: "parsons",
  before: "import math",
  lines: ["a = 1", "b = a + 1", "print(b)"],
  distractors: ["a = 5"],
});
const fill = item({
  kind: "fill",
  code: "x = ___\nprint(x)",
  options: ["1", "2", "3"],
  right: 1,
});
const bug = item({
  kind: "bug",
  lines: ["a = 1", "b = a +", "print(b)"],
  bug: 1,
  fix: "b = a + 1",
  why: "Falta un operando.",
});

const sources = (it: Item) =>
  checksOf(it).map((check) => check.programs.map((p) => p.source));

const same: Runner = (programs) =>
  programs.map(() => ({ ok: true, out: "1", error: "" }));
const brokenSum = (program: Program) => program.source.includes("a +\n");

const runner =
  (fails: (program: Program) => boolean = () => false): Runner =>
  (programs) =>
    programs.map((program): Outcome =>
      fails(program)
        ? { ok: false, out: "", error: "SyntaxError" }
        : { ok: true, out: `ok:${program.source}`, error: "" },
    );

describe("solution", () => {
  test.each([
    ["parsons", parsons, "import math\na = 1\nb = a + 1\nprint(b)"],
    ["fill", fill, "x = 2\nprint(x)"],
    ["bug", bug, "a = 1\nb = a + 1\nprint(b)"],
  ])("assembles the right code of a %s item", (_kind, it, code) => {
    expect(solution(it as Parameters<typeof solution>[0])).toBe(code);
  });
});

describe("checksOf", () => {
  test("a choice has no code to check", () => {
    const choice = item({ kind: "choice", options: ["a", "b"], right: 0 });
    expect(checksOf(choice)).toEqual([]);
  });

  test("a parsons item tries each neighbouring swap and each distractor at every position", () => {
    const [right, order, distractor] = sources(parsons);
    expect(right).toEqual(["import math\na = 1\nb = a + 1\nprint(b)"]);
    expect(order).toHaveLength(1 + 2);
    expect(order![1]).toBe("import math\nb = a + 1\na = 1\nprint(b)");
    expect(distractor).toHaveLength(4);
    expect(distractor![0]).toBe(
      "import math\na = 5\na = 1\nb = a + 1\nprint(b)",
    );
  });

  test("a swap of two equal lines is not a different order", () => {
    const twice = item({
      kind: "parsons",
      lines: ["x += 1", "x += 1", "print(x)"],
      before: "x = 0",
    });
    expect(sources(twice)[1]).toHaveLength(1 + 1);
  });

  test("a fill item compares each wrong option with the right one", () => {
    const [, first, second] = sources(fill);
    expect(first).toEqual(["x = 2\nprint(x)", "x = 1\nprint(x)"]);
    expect(second).toEqual(["x = 2\nprint(x)", "x = 3\nprint(x)"]);
  });

  test("a bug item compares the snippet with and without the bug", () => {
    expect(sources(bug)[1]).toEqual([
      "a = 1\nb = a + 1\nprint(b)",
      "a = 1\nb = a +\nprint(b)",
    ]);
  });
});

describe("verify", () => {
  test("passes when the right code runs and every claim holds", () => {
    expect(verify([parsons, fill, bug], runner(brokenSum))).toEqual([]);
  });

  test("names the item and the claim when the right code fails", () => {
    const problems = verify(
      [fill],
      runner((program) => program.source.startsWith("x = 2")),
    );
    expect(problems[0]).toBe("l:x: the right code runs: fails: SyntaxError");
  });

  test("flags a distractor that is not valid at any position", () => {
    const problems = verify(
      [parsons],
      runner((program) => program.source.includes("a = 5")),
    );
    expect(problems).toEqual([
      expect.stringContaining('the distractor "a = 5" is valid code'),
    ]);
  });

  test("flags an order that works as well as the right one", () => {
    const problems = verify([parsons], same);
    expect(problems).toEqual([
      expect.stringContaining("swapping lines 1 and 2 gives the same output"),
    ]);
  });

  test("flags a wrong option that behaves like the right one and a bug that changes nothing", () => {
    const problems = verify([fill, bug], same);
    expect(problems).toEqual([
      expect.stringContaining('the option "1" is wrong'),
      expect.stringContaining('the option "3" is wrong'),
      expect.stringContaining("the wrong line is a bug"),
    ]);
  });
});
