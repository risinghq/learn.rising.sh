import { DefaultScheduler, Rating } from "ts-fsrs";

import type { Item } from "./item.ts";

export const MAX_SESSION = 15;

/** One answer the learner gave. `at` is in Unix milliseconds. */
export interface Review {
  item: string;
  at: number;
  correct: boolean;
}

export interface SessionInput {
  /** Every item of the course. */
  bank: Item[];
  /** Every answer so far, in any order. The scheduler replays them. */
  log: Review[];
  /** The lessons the learner has finished. */
  done: string[];
  /** The time of the session, in Unix milliseconds. */
  now: number;
  /** Items wanted, at most `MAX_SESSION`. */
  size?: number;
}

/**
 * FSRS-6 with learning steps disabled returns whole-day intervals. A miss is
 * due the next day, and a first known answer is due in three days.
 */
const scheduler = DefaultScheduler({
  version: "FSRS-6",
  enableShortTerm: false,
});

type Fsrs = Awaited<typeof scheduler>;

function dueAt(fsrs: Fsrs, reviews: Review[]): number {
  const ordered = reviews.toSorted((a, b) => a.at - b.at);
  let card = fsrs.newCard({ now: new Date(ordered[0]!.at) });
  for (const review of ordered) {
    const grade = review.correct ? Rating.Good : Rating.Again;
    card = fsrs.review({ card, grade, now: new Date(review.at) }).card;
  }
  return card.dueAt.getTime();
}

/** One item from each lesson in turn, so a session does not drill a single lesson. */
function interleave(items: Item[]): Item[] {
  const queues = new Map<string, Item[]>();
  for (const item of items) {
    const queue = queues.get(item.lesson) ?? [];
    queue.push(item);
    queues.set(item.lesson, queue);
  }
  const turns: Item[] = [];
  for (let i = 0; turns.length < items.length; i++) {
    for (const queue of queues.values()) {
      if (i < queue.length) turns.push(queue[i]!);
    }
  }
  return turns;
}

/**
 * The next session: the items due for review, the longest overdue first, then
 * new items from the lessons the learner has finished. A prediction is a bet
 * with no right answer, so it is asked once and never reviewed.
 */
export async function planSession(input: SessionInput): Promise<Item[]> {
  const fsrs = await scheduler;
  const size = Math.max(0, Math.min(input.size ?? MAX_SESSION, MAX_SESSION));
  const finished = new Set(input.done);

  const reviews = new Map<string, Review[]>();
  for (const review of input.log) {
    reviews.set(review.item, [...(reviews.get(review.item) ?? []), review]);
  }

  const due: { item: Item; at: number }[] = [];
  const unseen: Item[] = [];
  for (const item of input.bank) {
    if (!finished.has(item.lesson)) continue;
    const own = reviews.get(item.id);
    if (!own) unseen.push(item);
    else if (item.kind !== "predict") due.push({ item, at: dueAt(fsrs, own) });
  }

  const overdue = due
    .filter(({ at }) => at <= input.now)
    .toSorted((a, b) => a.at - b.at || a.item.id.localeCompare(b.item.id))
    .map(({ item }) => item);
  return [...overdue, ...interleave(unseen)].slice(0, size);
}
