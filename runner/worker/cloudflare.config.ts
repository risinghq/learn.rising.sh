import { execFileSync } from "node:child_process";

import {
  bindings,
  defineConfig,
  defineContainer,
  exports,
  triggers,
} from "cf/config";

import * as entrypoint from "./src/index.ts" with { type: "cf-worker" };
import { WORKER_FIRST } from "./src/routes.ts";

// The Python and uv versions of the image are those of mise.toml.
const miseVersion = (tool: string) =>
  execFileSync("mise", ["current", tool], { encoding: "utf8" }).trim();

// The instance type and count set what the Worker counts as spend
// (src/container.ts), so they are declared once here and passed to `env`.
const INSTANCE_TYPE = "standard-2";
const INSTANCES = 2;

const runner = defineContainer({
  name: "duo-runner",
  image: {
    dockerfile: "../Dockerfile",
    buildContext: "../..",
    buildVars: {
      PYTHON_VERSION: miseVersion("python"),
      UV_VERSION: miseVersion("uv"),
    },
  },
  instanceType: INSTANCE_TYPE,
  maxInstances: INSTANCES,
});

// The host of the site. Accounts, progress and the runs of all
// courses go through it.
const HOME_HOST = "edu.rising.sh";

export default defineConfig({
  worker: {
    name: "duo",
    // The Worker is served only on the site's domain.
    domains: [HOME_HOST],
    workersDev: false,
    compatibilityDate: "2026-10-01",
    entrypoint,
    // Workers Logs stores only what src/log.ts writes. The invocation log
    // carries the request, so it is off.
    observability: {
      enabled: true,
      logs: { enabled: true, invocationLogs: false },
    },
    // site/ (wrangler.config.ts) is served from this same Worker.
    // Only the routes of WORKER_FIRST invoke it.
    assets: { runWorkerFirst: WORKER_FIRST },
    triggers: [triggers.scheduled({ schedule: "17 3 * * *" })],
    env: {
      ASSETS: bindings.assets(),
      // Accounts, progress and attempts (src/schema.sql).
      DB: bindings.d1({ name: "qiskit-guides" }),
      // The OAuth clients are created in the Google and GitHub accounts, and their
      // secrets are not written here.
      GOOGLE_CLIENT_ID: bindings.secret(),
      GOOGLE_CLIENT_SECRET: bindings.secret(),
      GITHUB_CLIENT_ID: bindings.secret(),
      GITHUB_CLIENT_SECRET: bindings.secret(),
      AUTH_PER_MINUTE: bindings.text("10"),
      AUTH_SESSION_DAYS: bindings.text("30"),
      SIGNED_IN_IP_FACTOR: bindings.text("4"),
      ATTEMPT_RETENTION_DAYS: bindings.text("180"),
      ACCOUNT_RETENTION_DAYS: bindings.text("730"),
      // The Turnstile widget secret is not written here: it is created in the account.
      TURNSTILE_SECRET: bindings.secret(),
      // The site key is public and is copied from the Turnstile widget.
      TURNSTILE_SITE_KEY: bindings.text("0x4AAAAAAFeMJBfEJZkBlG8m"),
      RATE_PER_MINUTE: bindings.text("30"),
      RATE_PER_DAY: bindings.text("1000"),
      MAX_CODE_BYTES: bindings.text("20000"),
      // The estimated spend of the month stays under this cap. The Workers
      // Paid bill (5 USD) is not counted in it.
      MONTHLY_BUDGET_USD: bindings.text("2"),
      // Whoever does not maintain the site spends up to this share of the budget, and of it
      // no more than 1/PUBLIC_BUDGET_DAYS in one day. The rest is for the maintainers.
      PUBLIC_BUDGET_SHARE: bindings.text("0.75"),
      PUBLIC_BUDGET_DAYS: bindings.text("15"),
      INSTANCE_TYPE: bindings.text(INSTANCE_TYPE),
      INSTANCES: bindings.text(String(INSTANCES)),
      // 10 s of work, the instance start and a retry after a 503.
      RESERVED_BUSY_SECONDS: bindings.text("30"),
      // Numeric GitHub ids, separated by commas, of the people who maintain the site.
      // 20960328 is the id of totallynotdavid.
      MAINTAINERS: bindings.text("20960328"),
      SESSION_HOURS: bindings.text("8"),
    },
    exports: {
      Runner: exports.durableObject({ storage: "sqlite", container: runner }),
      RateLimiter: exports.durableObject({ storage: "sqlite" }),
      Budget: exports.durableObject({ storage: "sqlite" }),
    },
  },
  containers: [runner],
});
