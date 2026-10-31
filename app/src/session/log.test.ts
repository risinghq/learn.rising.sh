import { describe, expect, it } from "vitest";

import { compactReviews, type Review } from "../../../site/progress.ts";

const review = (item: string, at: number, correct = true): Review => ({
  item,
  at,
  correct,
});

describe("compactReviews", () => {
  it("keeps the 4 latest answers of an item, oldest first", () => {
    const log = [1, 2, 3, 4, 5, 6].map((at) => review("a", at));
    expect(compactReviews(log).map((r) => r.at)).toEqual([3, 4, 5, 6]);
  });

  it("keeps the 800 latest answers overall", () => {
    const log = Array.from({ length: 900 }, (_, k) => review(`i${k}`, k));
    const kept = compactReviews(log);
    expect(kept).toHaveLength(800);
    expect(kept[0]!.at).toBe(100);
    expect(kept.at(-1)!.at).toBe(899);
  });

  it("does not depend on the order it is given", () => {
    const log = [review("a", 2, false), review("b", 1), review("a", 3)];
    expect(compactReviews(log)).toEqual(compactReviews(log.toReversed()));
  });
});
