import type { Item } from "./item.ts";
import { BLANK } from "./present.ts";

export interface Program {
  lang: "python" | "qasm";
  source: string;
}

export interface Outcome {
  ok: boolean;
  out: string;
  error: string;
}

export type Runner = (programs: Program[]) => Outcome[];

type Coded = Extract<Item, { kind: "parsons" | "fill" | "bug" }>;

interface Check {
  claim: string;
  programs: Program[];
  verdict: (outcomes: Outcome[]) => string | null;
}

type Parsons = Extract<Item, { kind: "parsons" }>;

const assemble = (item: Parsons, lines: string[]): string =>
  (item.before ? [item.before, ...lines] : lines).join("\n");

export function solution(item: Coded): string {
  switch (item.kind) {
    case "parsons":
      return assemble(item, item.lines);
    case "fill":
      return item.code.replace(BLANK, item.options[item.right]!);
    case "bug":
      return item.lines
        .map((line, i) => (i === item.bug ? item.fix : line))
        .join("\n");
  }
}

export function broken(item: Extract<Item, { kind: "bug" }>): string {
  return item.lines.join("\n");
}

const failed = (outcome: Outcome | undefined): string | null =>
  outcome?.ok ? null : `fails: ${outcome?.error ?? "no outcome"}`;

const insertions = (lines: string[], line: string): string[][] =>
  Array.from({ length: lines.length + 1 }, (_, i) => [
    ...lines.slice(0, i),
    line,
    ...lines.slice(i),
  ]);

const swaps = (lines: string[]): { at: number; lines: string[] }[] =>
  lines.flatMap((line, at) => {
    const next = lines[at + 1];
    if (next === undefined || next === line) return [];
    return [
      {
        at,
        lines: [...lines.slice(0, at), next, line, ...lines.slice(at + 2)],
      },
    ];
  });

export function checksOf(item: Item): Check[] {
  if (item.kind !== "parsons" && item.kind !== "fill" && item.kind !== "bug")
    return [];
  const { lang } = item;
  const right = solution(item);
  const checks: Check[] = [
    {
      claim: "the right code runs",
      programs: [{ lang, source: right }],
      verdict: ([outcome]) => failed(outcome),
    },
  ];

  if (item.kind === "parsons") {
    // If no neighbouring swap changes what the code does, no other order does
    // either, so the right order is the only one.
    const swapped = swaps(item.lines);
    checks.push({
      claim: "no other order of two neighbouring lines works",
      programs: [
        right,
        ...swapped.map(({ lines }) => assemble(item, lines)),
      ].map((source) => ({
        lang,
        source,
      })),
      verdict: ([good, ...others]) => {
        const same = others.findIndex(
          (other) => other.ok && other.out === good?.out,
        );
        return same < 0
          ? null
          : `swapping lines ${swapped[same]!.at + 1} and ${swapped[same]!.at + 2} gives the same output`;
      },
    });
    for (const line of item.distractors) {
      checks.push({
        claim: `the distractor ${JSON.stringify(line)} is valid code`,
        programs: insertions(item.lines, line).map((lines) => ({
          lang,
          source: assemble(item, lines),
        })),
        verdict: (outcomes) =>
          outcomes.some((outcome) => outcome.ok)
            ? null
            : `fails at every position: ${outcomes.at(-1)?.error}`,
      });
    }
  }

  if (item.kind === "fill") {
    item.options.forEach((option, i) => {
      if (i === item.right) return;
      checks.push({
        claim: `the option ${JSON.stringify(option)} is wrong`,
        programs: [
          { lang, source: right },
          { lang, source: item.code.replace(BLANK, option) },
        ],
        verdict: ([good, other]) =>
          other?.ok && other.out === good?.out
            ? "gives the same output as the right option"
            : null,
      });
    });
  }

  if (item.kind === "bug") {
    checks.push({
      claim: "the wrong line is a bug",
      programs: [
        { lang, source: right },
        { lang, source: broken(item) },
      ],
      verdict: ([good, bad]) =>
        bad?.ok && bad.out === good?.out
          ? "the snippet gives the same output with the bug"
          : null,
    });
  }
  return checks;
}

export function verify(items: Item[], run: Runner): string[] {
  const checks = items.flatMap((item) =>
    checksOf(item).map((check) => ({ item, check })),
  );
  const outcomes = run(checks.flatMap(({ check }) => check.programs));
  const problems: string[] = [];
  let at = 0;
  for (const { item, check } of checks) {
    const mine = outcomes.slice(at, at + check.programs.length);
    at += check.programs.length;
    const problem = check.verdict(mine);
    if (problem) problems.push(`${item.id}: ${check.claim}: ${problem}`);
  }
  return problems;
}
