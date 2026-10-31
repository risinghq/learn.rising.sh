import { z } from "zod";

import { BLANK } from "./present.ts";

const text = z.string().trim().min(1);

const base = {
  id: z.string().regex(/^[a-z0-9-]+:[a-z0-9-]+$/, {
    message: "must be lowercase letters, digits and dashes",
  }),
  lesson: z.string().regex(/^[a-z0-9-]+$/),
  prompt: text,
  hint: text.optional(),
};

const options = (min: number, max: number) =>
  z
    .array(text)
    .min(min)
    .max(max)
    .refine((list) => new Set(list).size === list.length, {
      message: "options must differ from each other",
    });

const index = z.number().int().min(0);

const lang = z.enum(["python", "qasm"]).default("python");

const choice = z
  .strictObject({
    ...base,
    kind: z.literal("choice"),
    options: options(2, 6),
    right: index,
    why: text.optional(),
    wrong: z.array(text.nullable()).optional(),
  })
  .refine((item) => item.right < item.options.length, {
    path: ["right"],
    message: "right must be the index of an option",
  })
  .refine((item) => !item.wrong || item.wrong.length <= item.options.length, {
    path: ["wrong"],
    message: "wrong has more entries than options",
  });

const numeric = z.strictObject({
  ...base,
  kind: z.literal("numeric"),
  answer: z.number().finite().min(0, "a numeric answer is not negative"),
  tol: z.number().finite().min(0).optional(),
  why: text.optional(),
  unit: text.optional(),
});

const predict = z.strictObject({
  ...base,
  kind: z.literal("predict"),
  options: options(2, 6),
  after: text,
});

const parsons = z.strictObject({
  ...base,
  kind: z.literal("parsons"),
  lang,
  before: z.string().min(1).optional(),
  lines: z.array(z.string().min(1)).min(2).max(10),
  distractors: z.array(z.string().min(1)).max(4).default([]),
  why: text.optional(),
});

const fill = z
  .strictObject({
    ...base,
    kind: z.literal("fill"),
    lang,
    code: z.string().min(1),
    options: options(3, 4),
    right: index,
    why: text.optional(),
  })
  .refine((item) => item.code.split(BLANK).length === 2, {
    path: ["code"],
    message: `code must hold exactly one ${BLANK}`,
  })
  .refine((item) => item.right < item.options.length, {
    path: ["right"],
    message: "right must be the index of an option",
  });

const bug = z
  .strictObject({
    ...base,
    kind: z.literal("bug"),
    lang,
    lines: z.array(z.string().min(1)).min(3).max(10),
    bug: index,
    fix: z.string().min(1),
    why: text,
  })
  .refine((item) => item.bug < item.lines.length, {
    path: ["bug"],
    message: "bug must be the index of a line",
  })
  .refine((item) => item.fix !== item.lines[item.bug], {
    path: ["fix"],
    message: "fix must differ from the wrong line",
  });

export const itemSchema = z.discriminatedUnion("kind", [
  choice,
  numeric,
  predict,
  parsons,
  fill,
  bug,
]);

export type Item = z.output<typeof itemSchema>;
export type ItemKind = Item["kind"];
export type ItemOf<K extends ItemKind> = Extract<Item, { kind: K }>;

export interface Bank {
  items: Item[];
}
