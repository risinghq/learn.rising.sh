import type { Item, ItemOf } from "./item.ts";

export interface Result {
  correct: boolean;
  feedback: string;
}

export type Answer = number | string | string[];

const EPSILON = 1e-9;

const ok = (feedback?: string): Result => ({
  correct: true,
  feedback: feedback ?? "Correcto.",
});

const no = (feedback?: string): Result => ({
  correct: false,
  feedback: feedback ?? "Incorrecto.",
});

const isIndex = (answer: Answer, length: number): answer is number =>
  typeof answer === "number" &&
  Number.isInteger(answer) &&
  answer >= 0 &&
  answer < length;

export function gradeChoice(item: ItemOf<"choice">, answer: Answer): Result {
  if (!isIndex(answer, item.options.length)) return no("Elige una opción.");
  if (answer === item.right) return ok(item.why);
  return no(item.wrong?.[answer] ?? undefined);
}

export function gradePredict(item: ItemOf<"predict">, answer: Answer): Result {
  if (!isIndex(answer, item.options.length)) return no("Elige una opción.");
  return ok(item.after);
}

const NUMBER = /^[+-]?(\d+([.,]\d*)?|[.,]\d+)$/;

export function parseNumber(text: string): number {
  const trimmed = text.trim();
  return NUMBER.test(trimmed) ? Number(trimmed.replace(",", ".")) : Number.NaN;
}

export function gradeNumeric(item: ItemOf<"numeric">, answer: Answer): Result {
  const value = typeof answer === "string" ? parseNumber(answer) : answer;
  if (typeof value !== "number" || !Number.isFinite(value))
    return no("Escribe un número.");
  const within = Math.abs(value - item.answer) <= (item.tol ?? 0) + EPSILON;
  if (within) return ok(item.why);
  return no(item.hint ? `Incorrecto. ${item.hint}` : undefined);
}

export function gradeParsons(item: ItemOf<"parsons">, answer: Answer): Result {
  if (!Array.isArray(answer)) return no("Ordena las líneas.");
  const inPlace = item.lines.filter((line, i) => answer[i] === line).length;
  if (answer.length === item.lines.length && inPlace === item.lines.length)
    return ok(item.why);
  const count = `Tienes ${inPlace} de ${item.lines.length} líneas en su sitio.`;
  return no(item.why ? `${count} ${item.why}` : count);
}

export function gradeFill(item: ItemOf<"fill">, answer: Answer): Result {
  if (!isIndex(answer, item.options.length)) return no("Elige una opción.");
  return answer === item.right ? ok(item.why) : no(item.why);
}

export function gradeBug(item: ItemOf<"bug">, answer: Answer): Result {
  if (!isIndex(answer, item.lines.length)) return no("Toca una línea.");
  if (answer === item.bug) return ok(item.why);
  return no(`La línea ${answer + 1} está bien. Busca otra.`);
}

export function grade(item: Item, answer: Answer): Result {
  switch (item.kind) {
    case "choice":
      return gradeChoice(item, answer);
    case "numeric":
      return gradeNumeric(item, answer);
    case "predict":
      return gradePredict(item, answer);
    case "parsons":
      return gradeParsons(item, answer);
    case "fill":
      return gradeFill(item, answer);
    case "bug":
      return gradeBug(item, answer);
  }
}
