import { describe, expect, test } from "vitest";

import { type Answer, grade } from "./grade.ts";
import { type Item, itemSchema } from "./item.ts";

const make = (fields: object): Item =>
  itemSchema.parse({ id: "l:x", lesson: "l", prompt: "p", ...fields });

const choice = make({
  kind: "choice",
  options: ["a", "b", "c"],
  right: 1,
  why: "Porque b.",
  wrong: ["No es a.", null],
});
const numeric = make({
  kind: "numeric",
  answer: 2.7,
  tol: 0.01,
  hint: "Eleva.",
});
const exact = make({ kind: "numeric", answer: 4 });
const predict = make({
  kind: "predict",
  options: ["x", "y"],
  after: "Anotado.",
});
const parsons = make({
  kind: "parsons",
  lines: ["a = 1", "for i in range(2):", "    a += i", "print(a)"],
  distractors: ["a = 2"],
  why: "El bucle va sangrado.",
});
const fill = make({
  kind: "fill",
  code: "x = ___",
  options: ["1", "2", "3"],
  right: 2,
  why: "Es 3.",
});
const bug = make({
  kind: "bug",
  lines: ["a = 1", "b = a +", "c = b"],
  bug: 1,
  fix: "b = a + 1",
  why: "Falta un operando.",
});

interface Case {
  name: string;
  item: Item;
  answer: Answer;
  correct: boolean;
  feedback?: string;
}

const cases: Case[] = [
  {
    name: "choice right",
    item: choice,
    answer: 1,
    correct: true,
    feedback: "Porque b.",
  },
  {
    name: "choice wrong with a reason",
    item: choice,
    answer: 0,
    correct: false,
    feedback: "No es a.",
  },
  {
    name: "choice wrong without a reason",
    item: choice,
    answer: 2,
    correct: false,
    feedback: "Incorrecto.",
  },
  {
    name: "choice out of range",
    item: choice,
    answer: 3,
    correct: false,
    feedback: "Elige una opción.",
  },
  { name: "choice negative", item: choice, answer: -1, correct: false },
  { name: "choice fraction", item: choice, answer: 1.5, correct: false },
  { name: "choice NaN", item: choice, answer: Number.NaN, correct: false },
  { name: "choice text", item: choice, answer: "1", correct: false },

  { name: "numeric exact", item: numeric, answer: 2.7, correct: true },
  {
    name: "numeric at the tolerance",
    item: numeric,
    answer: 2.71,
    correct: true,
  },
  {
    name: "numeric beyond the tolerance",
    item: numeric,
    answer: 2.72,
    correct: false,
    feedback: "Incorrecto. Eleva.",
  },
  {
    name: "numeric decimal comma",
    item: numeric,
    answer: "2,7",
    correct: true,
  },
  {
    name: "numeric decimal point and spaces",
    item: numeric,
    answer: " 2.70 ",
    correct: true,
  },
  {
    name: "numeric empty text",
    item: numeric,
    answer: "",
    correct: false,
    feedback: "Escribe un número.",
  },
  { name: "numeric words", item: numeric, answer: "dos", correct: false },
  {
    name: "numeric hexadecimal",
    item: numeric,
    answer: "0x10",
    correct: false,
  },
  {
    name: "numeric two commas",
    item: numeric,
    answer: "2,7,1",
    correct: false,
  },
  {
    name: "numeric infinity",
    item: numeric,
    answer: Number.POSITIVE_INFINITY,
    correct: false,
  },
  { name: "numeric NaN", item: numeric, answer: Number.NaN, correct: false },
  { name: "numeric list", item: numeric, answer: ["2.7"], correct: false },
  {
    name: "numeric without tolerance, float noise",
    item: make({ kind: "numeric", answer: 0.3 }),
    answer: 0.1 + 0.2,
    correct: true,
  },
  {
    name: "numeric without tolerance, off",
    item: exact,
    answer: 4.001,
    correct: false,
  },

  {
    name: "predict any option",
    item: predict,
    answer: 0,
    correct: true,
    feedback: "Anotado.",
  },
  { name: "predict the other option", item: predict, answer: 1, correct: true },
  {
    name: "predict no option",
    item: predict,
    answer: 2,
    correct: false,
    feedback: "Elige una opción.",
  },

  {
    name: "parsons right",
    item: parsons,
    answer: ["a = 1", "for i in range(2):", "    a += i", "print(a)"],
    correct: true,
  },
  {
    name: "parsons two lines swapped",
    item: parsons,
    answer: ["a = 1", "    a += i", "for i in range(2):", "print(a)"],
    correct: false,
    feedback: "Tienes 2 de 4 líneas en su sitio. El bucle va sangrado.",
  },
  {
    name: "parsons lost the indentation",
    item: parsons,
    answer: ["a = 1", "for i in range(2):", "a += i", "print(a)"],
    correct: false,
  },
  {
    name: "parsons with the distractor",
    item: parsons,
    answer: ["a = 1", "a = 2", "for i in range(2):", "    a += i", "print(a)"],
    correct: false,
  },
  {
    name: "parsons a line short",
    item: parsons,
    answer: ["a = 1", "for i in range(2):", "    a += i"],
    correct: false,
    feedback: "Tienes 3 de 4 líneas en su sitio. El bucle va sangrado.",
  },
  { name: "parsons empty", item: parsons, answer: [], correct: false },
  {
    name: "parsons not a list",
    item: parsons,
    answer: "a = 1",
    correct: false,
    feedback: "Ordena las líneas.",
  },

  {
    name: "fill right",
    item: fill,
    answer: 2,
    correct: true,
    feedback: "Es 3.",
  },
  { name: "fill wrong", item: fill, answer: 0, correct: false },
  {
    name: "fill out of range",
    item: fill,
    answer: 3,
    correct: false,
    feedback: "Elige una opción.",
  },

  {
    name: "bug right line",
    item: bug,
    answer: 1,
    correct: true,
    feedback: "Falta un operando.",
  },
  {
    name: "bug another line",
    item: bug,
    answer: 0,
    correct: false,
    feedback: "La línea 1 está bien. Busca otra.",
  },
  {
    name: "bug past the last line",
    item: bug,
    answer: 3,
    correct: false,
    feedback: "Toca una línea.",
  },
];

describe("grade", () => {
  test.each(cases)("$name", ({ item, answer, correct, feedback }) => {
    const result = grade(item, answer);
    expect(result.correct).toBe(correct);
    if (feedback !== undefined) expect(result.feedback).toBe(feedback);
  });
});
