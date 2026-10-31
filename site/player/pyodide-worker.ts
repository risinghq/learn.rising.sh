// The Web Worker that runs and grades Python for the browser-graded courses.
//
// The page sends `warm` to load Pyodide ahead of the first run and `run` to grade. The worker
// answers `ready`, `started` (the learner's code begins, so the page's clock starts) and `result`.
// A code that never ends is stopped by the page ending this worker.
import { createGrader, type Pyodide, type Verdict } from "./pyodide-grader.ts";

export type ToWorker =
  | { type: "warm" }
  | {
      type: "run";
      id: number;
      code: string;
      check: string;
      mode: "run" | "check";
    };

export type FromWorker =
  | { type: "ready"; ms: number }
  | { type: "started"; id: number }
  | { type: "result"; id: number; verdict: Verdict }
  | { type: "failed"; id: number | null; message: string };

const scope = self as unknown as {
  addEventListener(
    type: "message",
    listener: (event: MessageEvent<ToWorker>) => void,
  ): void;
  postMessage(message: FromWorker): void;
};

// The vendored Pyodide sits beside the folder that holds this script.
const BASE = new URL("../vendor/pyodide/", self.location.href);

type Grader = ReturnType<typeof createGrader>;
let loading: Promise<Grader> | undefined;

function load(): Promise<Grader> {
  loading ??= (async () => {
    const start = performance.now();
    // A variable address keeps the bundler from inlining the runtime.
    const url = `${BASE.href}pyodide.mjs`;
    const { loadPyodide } = (await import(url)) as {
      loadPyodide(options: {
        indexURL: string;
        lockFileURL: string;
      }): Promise<Pyodide>;
    };
    const py = await loadPyodide({
      indexURL: BASE.href,
      lockFileURL: `${BASE.href}pyodide-lock.json`,
    });
    const grader = createGrader(py);
    scope.postMessage({
      type: "ready",
      ms: Math.round(performance.now() - start),
    });
    return grader;
  })();
  // A failed load is tried again on the next message.
  loading.catch(() => (loading = undefined));
  return loading;
}

scope.addEventListener("message", async ({ data }) => {
  if (data.type === "warm") {
    await load().catch(() => {});
    return;
  }
  try {
    const grader = await load();
    await grader.prepare(data.code, data.check);
    scope.postMessage({ type: "started", id: data.id });
    const verdict = grader.grade(data.code, data.check, data.mode);
    scope.postMessage({ type: "result", id: data.id, verdict });
  } catch (error) {
    scope.postMessage({
      type: "failed",
      id: data.id,
      message: error instanceof Error ? error.message : String(error),
    });
  }
});
