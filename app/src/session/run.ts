// The state of one drill session apart from the markup: what is asked next, what each answer earns
// and which answers go to the review log.
import type { Review } from "@site/progress.ts";

import type { Item } from "../../../drill/item.ts";

/** XP for an item answered right the first time, and for one answered right when it came back. */
export const XP_FIRST = 2;
export const XP_RETRY = 1;

export interface Turn {
  item: Item;
  /** True for an item that came back at the end after a miss. */
  retry: boolean;
}

export interface Run {
  turns: Turn[];
  /** Index of the turn on screen. */
  at: number;
  /** The first answer to each item, which is what the scheduler learns from. */
  reviews: Review[];
  xp: number;
  /** Items answered right the first time. */
  first: number;
}

export const begin = (items: Item[]): Run => ({
  turns: items.map((item) => ({ item, retry: false })),
  at: 0,
  reviews: [],
  xp: 0,
  first: 0,
});

export const turnOf = (run: Run): Turn | undefined => run.turns[run.at];

export const finished = (run: Run) => run.at >= run.turns.length;

/**
 * Records the answer to the turn on screen. A miss adds the item once at the end, and a miss on
 * that second try adds nothing.
 */
export function answer(run: Run, correct: boolean, now: number): Run {
  const turn = turnOf(run);
  if (!turn) return run;
  return {
    ...run,
    turns:
      correct || turn.retry
        ? run.turns
        : [...run.turns, { item: turn.item, retry: true }],
    reviews: turn.retry
      ? run.reviews
      : [...run.reviews, { item: turn.item.id, at: now, correct }],
    xp: run.xp + (correct ? (turn.retry ? XP_RETRY : XP_FIRST) : 0),
    first: run.first + (correct && !turn.retry ? 1 : 0),
  };
}

export const next = (run: Run): Run => ({ ...run, at: run.at + 1 });
