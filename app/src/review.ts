// Spaced review: an answered question comes back after 1, 3, 7 and 21 days, and a missed one tomorrow.
import type { Lesson } from "./model.ts";

const DAY = 864e5;
export const GAPS = [1, 3, 7, 21];
export const PER_DAY = 3;

export interface Box {
  box: number;
  due: number;
}
export type ReviewState = Record<string, Box>;

interface ChoiceAsk {
  kind: "choice";
  prompt: string;
  options: string[];
  right: number;
  why?: string;
  hint?: string;
}
export interface NumericAsk {
  kind: "numeric";
  prompt: string;
  answer: number;
  tol?: number;
  why?: string;
  hint?: string;
}
export type Ask = ChoiceAsk | NumericAsk;

export interface Question {
  id: string;
  lesson: Lesson;
  ask: Ask;
  due: number;
}

interface LessonFile {
  beats: { id: string; ask?: { kind: string } }[];
}

/** The questions of finished lessons that are new or due, the longest overdue first and the rest in a random order. */
export function dueQuestions(
  loaded: { lesson: Lesson; file: LessonFile }[],
  state: ReviewState,
  now: number,
  random: () => number,
): Question[] {
  const due: (Question & { jitter: number })[] = [];
  for (const { lesson, file } of loaded) {
    for (const beat of file.beats) {
      const ask = beat.ask as Ask | undefined;
      if (ask?.kind !== "choice" && ask?.kind !== "numeric") continue;
      const id = `${lesson.id}:${beat.id}`;
      const stored = state[id];
      if (!stored || stored.due <= now)
        due.push({
          id,
          lesson,
          ask,
          due: stored ? stored.due : 0,
          jitter: random(),
        });
    }
  }
  return due.toSorted((a, b) => a.due - b.due || a.jitter - b.jitter);
}

/** The state after an answer, and the days until the question returns. */
export function answered(
  state: ReviewState,
  id: string,
  correct: boolean,
  now: number,
) {
  const box = correct
    ? Math.min((state[id]?.box ?? -1) + 1, GAPS.length - 1)
    : 0;
  const days = correct ? GAPS[box] : 1;
  return { state: { ...state, [id]: { box, due: now + days * DAY } }, days };
}

export function numericRight(
  ask: NumericAsk,
  text: string,
): boolean | undefined {
  if (text.trim() === "") return undefined;
  const value = Number(text.replace(",", "."));
  if (!Number.isFinite(value)) return undefined;
  return (
    Math.abs(value - ask.answer) <=
    (ask.tol ?? 0.01) * Math.max(1, Math.abs(ask.answer))
  );
}
