import { spawn, spawnSync } from "node:child_process";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { type Harness, start as startWorker } from "./harness.ts";
import { signIn } from "./signin.ts";

const ROOT = path.join(import.meta.dirname, "../../..");
const EXERCISE = "p1-quickstart/ghz";
const hasUv = spawnSync("uv", ["--version"]).status === 0;

const scratch = mkdtempSync(path.join(tmpdir(), "rising-e2e-"));
const env = path.join(scratch, "venv");
const home = path.join(scratch, "home");
const folder = path.join(scratch, "learner");

interface Run {
  code: number;
  stdout: string;
  stderr: string;
}

// Runs `rising`. `onOutput` sees stdout as it arrives, for a command that waits.
function rising(
  args: string[],
  url: string,
  onOutput?: (stdout: string) => void,
): Promise<Run> {
  return new Promise((resolve, reject) => {
    const child = spawn(path.join(env, "bin/rising"), args, {
      cwd: folder,
      env: { PATH: process.env.PATH, XDG_CONFIG_HOME: home, RISING_URL: url },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
      onOutput?.(stdout);
    });
    child.stderr.on("data", (chunk) => (stderr += chunk));
    child.on("error", reject);
    child.on("close", (code) => resolve({ code: code ?? -1, stdout, stderr }));
  });
}

describe.skipIf(!hasUv)("rising", () => {
  let h: Harness;
  let url: string;

  beforeAll(async () => {
    // A built copy, not an editable one: the checks ship inside the wheel.
    const built = spawnSync(
      "uv",
      [
        "sync",
        "--locked",
        "--no-editable",
        "--project",
        path.join(ROOT, "cli"),
        "--reinstall-package",
        "rising",
        "--reinstall-package",
        "qgcheck",
      ],
      {
        env: { ...process.env, UV_PROJECT_ENVIRONMENT: env },
        encoding: "utf8",
      },
    );
    expect(built.status, built.stderr).toBe(0);
    h = await startWorker();
    url = await h.origin();
    mkdirSync(folder, { recursive: true });
  }, 600_000);

  afterAll(async () => {
    await h?.dispose();
    rmSync(scratch, { recursive: true, force: true });
  });

  it("logs in, pulls, tests, submits, reports status and logs out", async () => {
    const { cookie } = await signIn(h, "google", "learner-3f81a6c0");
    let approved = false;
    const login = await rising(["login"], url, (stdout) => {
      const code = /\?code=([A-Z2-9-]+)/.exec(stdout)?.[1];
      if (!code || approved) return;
      approved = true;
      void h.request("POST", "/auth/device/approve", {
        headers: { origin: "http://runner.test", cookie: cookie! },
        form: { code, decision: "approve" },
      });
    });
    expect(login.stderr).toBe("");
    expect(login.stdout).toContain("Sesión iniciada.");
    const saved = path.join(home, "rising/credentials.json");
    expect(statSync(saved).mode & 0o777).toBe(0o600);

    const pulled = await rising(["pull", EXERCISE], url);
    expect(pulled.stderr).toBe("");
    expect(pulled.code).toBe(0);
    const starter = readFileSync(
      path.join(ROOT, "exercises", EXERCISE, "starter.py"),
      "utf8",
    );
    expect(readFileSync(path.join(folder, "ghz.py"), "utf8")).toBe(starter);
    expect(readFileSync(path.join(folder, "enunciado.md"), "utf8")).toContain(
      "## Casos visibles",
    );
    expect((await rising(["pull", EXERCISE], url)).stderr).toContain("--force");

    const failing = await rising(["test"], url);
    expect(failing.code).toBe(1);
    expect(failing.stdout).toContain("✗ n = 2, 3 y 4");
    const refused = await rising(["submit"], url);
    expect(refused.code).toBe(1);
    expect(refused.stdout).not.toContain("XP");

    copyFileSync(
      path.join(ROOT, "exercises", EXERCISE, "solution.py"),
      path.join(folder, "ghz.py"),
    );
    const passing = await rising(["test"], url);
    expect(passing.stdout).toContain("✓ n = 2, 3 y 4");
    expect(passing.stdout).toContain("Pasó todos los casos.");
    expect(passing.code).toBe(0);
    const submitted = await rising(["submit"], url);
    expect(submitted.stderr).toBe("");
    expect(submitted.stdout).toContain("+10 XP. Hoy llevas 10 de 300.");
    expect((await rising(["submit"], url)).stdout).toContain("Ya ganaste XP");

    const status = await rising(["status"], url);
    expect(status.stdout).toContain("Racha: 1 día");
    expect(status.stdout).toContain("XP de hoy: 10 de 300");
    expect(status.stdout).toMatch(/1\. tú\s+10 XP/);

    const token = JSON.parse(readFileSync(saved, "utf8")).token as string;
    const headers = { authorization: `Bearer ${token}` };
    expect((await h.request("GET", "/api/me", { headers })).status).toBe(200);
    expect((await rising(["logout"], url)).stdout).toContain("Sesión cerrada.");
    expect(existsSync(saved)).toBe(false);
    expect((await h.request("GET", "/api/me", { headers })).status).toBe(401);
    expect((await rising(["status"], url)).stderr).toContain("rising login");
  }, 300_000);
});
