// The page's side of the Pyodide worker: one worker for the page, started when a browser-graded
// exercise is focused or run, so a page without one never downloads Pyodide.
import type { Verdict } from "./pyodide-grader.ts";
import type { FromWorker, ToWorker } from "./pyodide-worker.ts";

/** How long the learner's code may run, as the server's job allows. */
export const RUN_LIMIT_MS = 10_000;

/** Why a run gave no verdict: the code ran past the limit, or Python did not load. */
export class RunStopped extends Error {
  constructor(readonly why: "time" | "load") {
    super(why);
  }
}

interface Job {
  id: number;
  done: (verdict: Verdict) => void;
  fail: (error: RunStopped) => void;
  started: () => void;
  timer?: ReturnType<typeof setTimeout>;
}

let worker: Worker | null = null;
let job: Job | null = null;
let ids = 0;

function finish(): Job | null {
  const current = job;
  job = null;
  if (current) clearTimeout(current.timer);
  return current;
}

function spawn(): Worker {
  const w = new Worker("../player/pyodide-worker.js", { type: "module" });
  w.addEventListener("message", ({ data }: MessageEvent<FromWorker>) => {
    if (data.type === "ready" || !job || ("id" in data && data.id !== job.id))
      return;
    if (data.type === "started") {
      const current = job;
      current.started();
      current.timer = setTimeout(() => stop(current), RUN_LIMIT_MS);
    } else if (data.type === "result") {
      finish()?.done(data.verdict);
    } else {
      finish()?.fail(new RunStopped("load"));
    }
  });
  // A worker that cannot start, such as a missing script, ends the run the same way.
  w.addEventListener("error", () => {
    worker = null;
    finish()?.fail(new RunStopped("load"));
  });
  return w;
}

// Ending the worker is the only way to stop Python that does not return. The next run starts a
// new one, which loads Pyodide from the cache.
function stop(current: Job): void {
  if (job !== current) return;
  worker?.terminate();
  worker = null;
  finish()?.fail(new RunStopped("time"));
}

function send(message: ToWorker): void {
  worker ??= spawn();
  worker.postMessage(message);
}

/** Starts loading Pyodide so the first run finds it ready. */
export const warm = (): void => send({ type: "warm" });

const once = (
  code: string,
  check: string,
  mode: "run" | "check",
  started: () => void,
): Promise<Verdict> =>
  new Promise((done, fail) => {
    job = { id: ++ids, done, fail, started };
    send({ type: "run", id: job.id, code, check, mode });
  });

// Two exercises on a page share the worker, one run at a time.
let queue: Promise<unknown> = Promise.resolve();

/**
 * Runs or grades `code`. `started` is called when Pyodide is loaded and the code begins, which is
 * when the time limit starts.
 */
export function grade(
  code: string,
  check: string,
  mode: "run" | "check",
  started: () => void = () => {},
): Promise<Verdict> {
  const result = queue.then(() => once(code, check, mode, started));
  queue = result.catch(() => {});
  return result;
}
