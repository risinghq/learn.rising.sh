import type { ItemOf } from "./item.ts";

export const BLANK = "___";

function hash(text: string): number {
  let h = 0x811c9dc5;
  for (const ch of text) {
    h = Math.imul(h ^ ch.codePointAt(0)!, 0x01000193) >>> 0;
  }
  return h;
}

function random(seed: number): () => number {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * The lines of a `parsons` item, distractors included, in the order the
 * learner sees them. The same item and seed give the same order, and the order
 * never starts out solved.
 */
export function parsonsPool(item: ItemOf<"parsons">, seed: string): string[] {
  const pool = [...item.lines, ...item.distractors];
  const next = random(hash(`${seed}:${item.id}`));
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(next() * (i + 1));
    [pool[i], pool[j]] = [pool[j]!, pool[i]!];
  }
  const solved = item.lines.every((line, i) => pool[i] === line);
  if (solved && new Set(pool).size > 1) pool.push(pool.shift()!);
  return pool;
}
