import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterAll, describe, expect, test } from "vitest";

import type { Ask, Lesson } from "../site/player/lesson.ts";
import { ItemError, buildBank, extractAsks, parseAuthored } from "./bank.ts";

const asks: Record<string, Ask> = {
  first: {
    kind: "choice",
    prompt: "¿Cuál?",
    options: ["a", "b"],
    right: 1,
    why: ["Uno.", "Dos."],
    wrong: ["No es a."],
  },
  second: {
    kind: "numeric",
    prompt: "¿Cuánto?",
    answer: 4,
    tol: 0.1,
    hint: "Suma.",
  },
  third: {
    kind: "predict",
    prompt: "¿Qué sale?",
    options: ["x", "y"],
    after: "Anotado.",
  },
};

const lesson = (order: string[]): Lesson => ({
  id: "p9-demo",
  part: "Parte",
  section: "9.1",
  title: "Demo",
  beats: [
    ...order.map((name) => ({ id: name, say: "", ask: asks[name]! })),
    { id: "talk", say: "" },
    {
      id: "think",
      say: "",
      ask: { kind: "reflect" as const, prompts: ["¿Por qué?"] },
    },
    { id: "see", say: "", ask: { kind: "reveal" as const, prompt: "Mira." } },
  ],
});

describe("extractAsks", () => {
  test("keeps choice, numeric and predict asks and skips the rest", () => {
    const items = extractAsks(lesson(["first", "second", "third"]));
    expect(items.map((item) => item.kind)).toEqual([
      "choice",
      "numeric",
      "predict",
    ]);
    expect(items[0]).toMatchObject({
      lesson: "p9-demo",
      why: "Uno.\n\nDos.",
      wrong: ["No es a."],
    });
    expect(items[1]).toMatchObject({ answer: 4, tol: 0.1, hint: "Suma." });
  });

  test("an item keeps its id when the beats are reordered", () => {
    const before = extractAsks(lesson(["first", "second", "third"]));
    const after = extractAsks(lesson(["third", "first", "second"]));
    const byPrompt = (items: typeof before) =>
      Object.fromEntries(items.map((item) => [item.prompt, item.id]));
    expect(byPrompt(after)).toEqual(byPrompt(before));
  });

  test("ids differ between asks and between lessons", () => {
    const here = extractAsks(lesson(["first", "second", "third"]));
    const there = extractAsks({ ...lesson(["first"]), id: "p9-other" });
    const ids = [...here, ...there].map((item) => item.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test("an id does not change when the options are edited", () => {
    const edited = lesson(["first"]);
    (edited.beats[0]!.ask as Extract<Ask, { kind: "choice" }>).options = [
      "a",
      "b",
      "c",
    ];
    expect(extractAsks(edited)[0]!.id).toBe(
      extractAsks(lesson(["first"]))[0]!.id,
    );
  });
});

const good = {
  kind: "fill",
  id: "fill-one",
  prompt: "¿Qué falta?",
  code: "x = ___",
  options: ["1", "2", "3"],
  right: 0,
};

const FILE = "drill/items/qiskit/p9-demo.json";

const manyBroken = () =>
  parseAuthored(FILE, "p9-demo", {
    items: [{ ...good, right: 9 }, good, { ...good, id: "B" }],
  });

describe("parseAuthored", () => {
  test("gives an item its lesson and a full id", () => {
    const [item] = parseAuthored(FILE, "p9-demo", { items: [good] });
    expect(item).toMatchObject({
      id: "p9-demo:fill-one",
      lesson: "p9-demo",
      lang: "python",
    });
  });

  const malformed: [string, object, string][] = [
    ["a missing prompt", { ...good, prompt: undefined }, "items[0].prompt"],
    ["an unknown kind", { ...good, kind: "match" }, "items[0].kind"],
    ["a misspelled field", { ...good, option: ["1"] }, "items[0]"],
    ["two blanks", { ...good, code: "x = ___ + ___" }, "items[0].code"],
    ["no blank", { ...good, code: "x = 1" }, "items[0].code"],
    ["two options", { ...good, options: ["1", "2"] }, "items[0].options"],
    [
      "repeated options",
      { ...good, options: ["1", "1", "2"] },
      "items[0].options",
    ],
    ["a right index past the options", { ...good, right: 3 }, "items[0].right"],
    ["an id with spaces", { ...good, id: "Fill One" }, "items[0].id"],
    ["a missing id", { ...good, id: undefined }, "items[0].id"],
    ["a lesson set by hand", { ...good, lesson: "p1-x" }, "items[0].lesson"],
    [
      "a bug index past the lines",
      {
        kind: "bug",
        id: "b",
        prompt: "p",
        lines: ["a", "b", "c"],
        bug: 3,
        fix: "d",
        why: "w",
      },
      "items[0].bug",
    ],
    [
      "a bug with no change",
      {
        kind: "bug",
        id: "b",
        prompt: "p",
        lines: ["a", "b", "c"],
        bug: 1,
        fix: "b",
        why: "w",
      },
      "items[0].fix",
    ],
    [
      "a parsons item with one line",
      { kind: "parsons", id: "p", prompt: "p", lines: ["a"] },
      "items[0].lines",
    ],
  ];

  test.each(malformed)(
    "fails on %s with the file and the field",
    (_name, item, field) => {
      expect(() =>
        parseAuthored(FILE, "p9-demo", { items: [good, item] }),
      ).toThrow(
        new RegExp(
          `^${FILE.replaceAll(".", "\\.")}: ${field.replace("[0]", "[1]").replaceAll(/[[\].]/g, "\\$&")}: `,
        ),
      );
    },
  );

  test("reports every broken item, not only the first", () => {
    expect(manyBroken).toThrow(ItemError);
    expect(manyBroken).toThrow(/items\[0\]\.right[^]*items\[2\]\.id/);
  });

  test("fails when the file holds no list", () => {
    expect(() => parseAuthored(FILE, "p9-demo", { item: [] })).toThrow(
      `${FILE}: items: expected a list`,
    );
  });
});

const write = (path: string, data: unknown) => {
  mkdirSync(join(path, ".."), { recursive: true });
  writeFileSync(path, JSON.stringify(data));
};

describe("buildBank", () => {
  const root = mkdtempSync(join(tmpdir(), "drill-bank-"));
  afterAll(() => rmSync(root, { recursive: true, force: true }));

  const site = join(root, "site");
  const authored = join(root, "items");
  write(join(site, "demo", "course.json"), {
    parts: [{ lessons: [{ id: "p9-demo" }] }],
  });
  write(
    join(site, "demo", "lessons", "p9-demo", "lesson.json"),
    lesson(["first", "second"]),
  );

  test("puts the asks of a lesson before its authored items", () => {
    write(join(authored, "demo", "p9-demo.json"), { items: [good] });
    const { items } = buildBank("demo", { site, authored });
    expect(items.map((item) => item.kind)).toEqual([
      "choice",
      "numeric",
      "fill",
    ]);
  });

  test("fails on an authored file of no lesson, naming it", () => {
    write(join(authored, "demo", "p9-gone.json"), { items: [good] });
    expect(() => buildBank("demo", { site, authored })).toThrow(
      /p9-gone\.json: not a lesson of demo/,
    );
    rmSync(join(authored, "demo", "p9-gone.json"));
  });

  test("fails when two authored items share an id", () => {
    write(join(authored, "demo", "p9-demo.json"), { items: [good, good] });
    expect(() => buildBank("demo", { site, authored })).toThrow(
      /two items have the id p9-demo:fill-one/,
    );
  });
});
