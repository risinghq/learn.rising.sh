// Grades a learner's code on Pyodide with the same `qgcheck` Python the server's job uses.
//
// The worker builds its grader here from `py`, the Pyodide instance.
import browser from "../../qgcheck/browser.py" with { type: "text" };
import cases from "../../qgcheck/cases.py" with { type: "text" };
import init from "../../qgcheck/__init__.py" with { type: "text" };
import host from "../../qgcheck/host.py" with { type: "text" };
import source from "../../qgcheck/source.py" with { type: "text" };
import spec from "../../qgcheck/spec.py" with { type: "text" };
import wire from "../../qgcheck/wire.py" with { type: "text" };

export interface Verdict {
  passed: boolean;
  stdout: string;
  error: string | null;
  tests: {
    name: string;
    visible: boolean;
    passed: boolean;
    message: string | null;
    hint: number | null;
  }[];
  killed: "output" | null;
}

export interface Pyodide {
  FS: {
    mkdirTree(path: string): void;
    writeFile(path: string, data: string): void;
  };
  runPython(code: string): unknown;
  runPythonAsync(code: string): Promise<unknown>;
  loadPackagesFromImports(code: string): Promise<unknown>;
  globals: { set(name: string, value: unknown): void };
}

const FILES: Record<string, string> = {
  "__init__.py": init,
  "browser.py": browser,
  "cases.py": cases,
  "host.py": host,
  "source.py": source,
  "spec.py": spec,
  "wire.py": wire,
};

export function createGrader(py: Pyodide) {
  py.FS.mkdirTree("/qg/qgcheck");
  for (const [name, text] of Object.entries(FILES))
    py.FS.writeFile(`/qg/qgcheck/${name}`, text);
  py.runPython(
    "import os, sys\nos.environ['MPLBACKEND'] = 'Agg'\nsys.path.insert(0, '/qg')\nimport qgcheck.browser",
  );
  return {
    // Downloads the packages the check and the code import (numpy, scipy and matplotlib are in
    // the lock). Apart from `grade`, so the download does not count against the run's time limit.
    // They go one at a time: a code with a syntax error names no imports, and the check still does.
    async prepare(code: string, check: string): Promise<void> {
      await py.loadPackagesFromImports(check);
      await py.loadPackagesFromImports(code);
    },
    grade(code: string, check: string, mode: "run" | "check"): Verdict {
      py.globals.set("_qg_args", [code, check, mode]);
      return JSON.parse(
        py.runPython(
          "import qgcheck.browser as _b; _b.grade_json(*_qg_args)",
        ) as string,
      ) as Verdict;
    },
  };
}
