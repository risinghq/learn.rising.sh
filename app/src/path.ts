// The decisions of the path page, apart from the markup: what is done, what is next, what is locked.
import type { Lesson, Part } from "./model.ts";

export type NodeState = "done" | "current" | "locked";

export const lessonsOf = (parts: Part[]): Lesson[] =>
  parts.flatMap((p) => p.lessons);

/** The first lesson not done, in the order of the course. */
export const nextLesson = <T extends { id: string }>(
  lessons: T[],
  done: ReadonlySet<string>,
) => lessons.find((l) => !done.has(l.id));

export function stateOf(
  lesson: Lesson,
  next: Lesson | undefined,
  done: ReadonlySet<string>,
): NodeState {
  if (done.has(lesson.id)) return "done";
  return lesson === next ? "current" : "locked";
}

export const lessonHref = (slug: string, id: string) =>
  `/${slug}/lesson.html?l=${encodeURIComponent(id)}`;

/** A mission of a finished lesson that the learner has not marked. The project's notebooks have their own track. */
export function pendingMission(
  lessons: Lesson[],
  done: ReadonlySet<string>,
  marked: readonly string[],
) {
  for (const lesson of lessons) {
    if (!done.has(lesson.id)) continue;
    const mission = lesson.missions?.find(
      (m) => !m.notebook.includes("proyecto/") && !marked.includes(m.notebook),
    );
    if (mission) return { lesson, mission };
  }
  return undefined;
}

export const notebookCommand = (notebook: string) =>
  `uv run marimo edit ${notebook}`;

export const hours = (minutes: number) =>
  (minutes / 60).toLocaleString("es", { maximumFractionDigits: 1 });

export const minutesOf = (lessons: { minutes: number }[]) =>
  lessons.reduce((total, l) => total + l.minutes, 0);

/** "Parte I · Primeros pasos" splits into the label and the name. */
export function splitTitle(title: string): { label: string; name: string } {
  const [label, ...name] = title.split(" · ");
  return { label, name: name.join(" · ") || label };
}
