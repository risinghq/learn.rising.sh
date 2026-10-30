import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { ZodError } from "zod";

import type { Ask, Lesson } from "../site/player/lesson.ts";
import { type Bank, type Item, itemSchema } from "./item.ts";

export const SITE = resolve(import.meta.dirname, "..", "site");
export const AUTHORED = resolve(import.meta.dirname, "items");

export class ItemError extends Error {}

const read = (path: string): unknown => JSON.parse(readFileSync(path, "utf8"));

export function askId(lesson: string, kind: string, prompt: string): string {
  const hash = createHash("sha256")
    .update(prompt.normalize("NFC"))
    .digest("hex");
  return `${lesson}:${kind}-${hash.slice(0, 8)}`;
}

const joined = (text: string | string[] | undefined): string | undefined =>
  Array.isArray(text) ? text.join("\n\n") : text;

function fromAsk(lesson: string, ask: Ask): Item | undefined {
  if (ask.kind !== "choice" && ask.kind !== "numeric" && ask.kind !== "predict")
    return undefined;
  const common = {
    id: askId(lesson, ask.kind, ask.prompt),
    lesson,
    prompt: ask.prompt,
    ...(ask.hint === undefined ? {} : { hint: ask.hint }),
  };
  const why = joined("why" in ask ? ask.why : undefined);
  const withWhy = why === undefined ? {} : { why };
  switch (ask.kind) {
    case "choice":
      return itemSchema.parse({
        ...common,
        ...withWhy,
        kind: "choice",
        options: ask.options,
        right: ask.right,
        ...(ask.wrong ? { wrong: ask.wrong } : {}),
      });
    case "numeric":
      return itemSchema.parse({
        ...common,
        ...withWhy,
        kind: "numeric",
        answer: ask.answer,
        ...(ask.tol === undefined ? {} : { tol: ask.tol }),
        ...(ask.unit === undefined ? {} : { unit: ask.unit }),
      });
    case "predict":
      return itemSchema.parse({
        ...common,
        kind: "predict",
        options: ask.options,
        after: ask.after,
      });
  }
}

export function extractAsks(lesson: Lesson): Item[] {
  const items: Item[] = [];
  for (const beat of lesson.beats) {
    const item = beat.ask && fromAsk(lesson.id, beat.ask);
    if (item) items.push(item);
  }
  return items;
}

const field = (path: PropertyKey[]): string =>
  path.reduce<string>(
    (acc, key) =>
      typeof key === "number"
        ? `${acc}[${key}]`
        : acc
          ? `${acc}.${String(key)}`
          : String(key),
    "",
  );

const issues = (
  file: string,
  error: ZodError,
  prefix: PropertyKey[] = [],
): string[] =>
  error.issues.map(
    (issue) =>
      `${file}: ${field([...prefix, ...issue.path])}: ${issue.message}`,
  );

/**
 * The items of one authored file. The file holds `{"items": [...]}`; each
 * item names itself with an `id` local to the lesson, and the file name says
 * the lesson.
 */
export function parseAuthored(
  file: string,
  lesson: string,
  data: unknown,
): Item[] {
  const raw = (data as { items?: unknown } | null)?.items;
  if (!Array.isArray(raw)) {
    throw new ItemError(`${file}: items: expected a list`);
  }
  const problems: string[] = [];
  const items: Item[] = [];
  raw.forEach((entry: unknown, i) => {
    if (typeof entry === "object" && entry !== null && "lesson" in entry) {
      problems.push(`${file}: items[${i}].lesson: set by the file name`);
      return;
    }
    const local = (entry as { id?: unknown } | null)?.id;
    const record = {
      ...(entry as object),
      lesson,
      id: `${lesson}:${typeof local === "string" ? local : ""}`,
    };
    const parsed = itemSchema.safeParse(record);
    if (parsed.success) {
      items.push(parsed.data);
      return;
    }
    problems.push(...issues(file, parsed.error, ["items", i]));
  });
  if (problems.length > 0) throw new ItemError(problems.join("\n"));
  return items;
}

interface Course {
  parts: { lessons: { id: string }[] }[];
}

export interface Roots {
  site: string;
  authored: string;
}

export const ROOTS: Roots = { site: SITE, authored: AUTHORED };

export function courses(site: string = SITE): string[] {
  return readdirSync(site).filter((slug) =>
    existsSync(join(site, slug, "course.json")),
  );
}

export function buildBank(course: string, roots: Roots = ROOTS): Bank {
  const dir = join(roots.site, course);
  const order = (read(join(dir, "course.json")) as Course).parts.flatMap(
    (part) => part.lessons.map((lesson) => lesson.id),
  );
  const authoredDir = join(roots.authored, course);
  const authored = existsSync(authoredDir) ? readdirSync(authoredDir) : [];
  for (const name of authored) {
    const id = name.replace(/\.json$/, "");
    if (!name.endsWith(".json") || !order.includes(id)) {
      throw new ItemError(
        `${join(authoredDir, name)}: not a lesson of ${course}`,
      );
    }
  }

  const items: Item[] = [];
  for (const id of order) {
    const lesson = read(join(dir, "lessons", id, "lesson.json")) as Lesson;
    try {
      items.push(...extractAsks(lesson));
    } catch (error) {
      if (!(error instanceof ZodError)) throw error;
      throw new ItemError(
        issues(join(dir, "lessons", id, "lesson.json"), error).join("\n"),
      );
    }
    const file = join(authoredDir, `${id}.json`);
    if (authored.includes(`${id}.json`))
      items.push(...parseAuthored(file, id, read(file)));
  }

  const seen = new Set<string>();
  for (const item of items) {
    if (seen.has(item.id))
      throw new ItemError(`${course}: two items have the id ${item.id}`);
    seen.add(item.id);
  }
  return { items };
}
