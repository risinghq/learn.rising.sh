// Finds the course that owns a lesson: the folder site/<course>/lessons/<id>.
import { existsSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const SITE = resolve(import.meta.dirname, "..", "site");

export function courseOf(lessonId: string): string {
  const course = readdirSync(SITE).find((slug) =>
    existsSync(join(SITE, slug, "lessons", lessonId)),
  );
  if (!course) throw new Error(`no course has the lesson ${lessonId}`);
  return course;
}

export function lessonDir(lessonId: string): string {
  return join(SITE, courseOf(lessonId), "lessons", lessonId);
}
