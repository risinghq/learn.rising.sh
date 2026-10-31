import { spawnSync } from "node:child_process";
import { join } from "node:path";

import { ItemError, buildBank, courses } from "./bank.ts";
import { type Outcome, type Program, type Runner, verify } from "./code.ts";

const HARNESS = join(import.meta.dirname, "run_code.py");

const runner: Runner = (programs: Program[]): Outcome[] => {
  const run = spawnSync("uv", ["run", "python", "-I", HARNESS], {
    input: JSON.stringify(programs),
    encoding: "utf8",
    maxBuffer: 1 << 28,
  });
  if (run.status !== 0) throw new Error(`run_code.py failed:\n${run.stderr}`);
  const reply = JSON.parse(run.stdout) as {
    qiskit: string;
    results: Outcome[];
  };
  if (!reply.qiskit.startsWith("2.6."))
    throw new Error(`Qiskit ${reply.qiskit}, not 2.6`);
  return reply.results;
};

try {
  const problems: string[] = [];
  for (const course of courses()) {
    problems.push(
      ...verify(buildBank(course).items, runner).map((p) => `${course}/${p}`),
    );
  }
  if (problems.length > 0) {
    console.error(problems.join("\n"));
    process.exit(1);
  }
  console.log("every authored item runs");
} catch (error) {
  if (!(error instanceof ItemError)) throw error;
  console.error(error.message);
  process.exit(1);
}
