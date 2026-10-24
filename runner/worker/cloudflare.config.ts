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

// Las versiones de Python y de uv de la imagen son las de mise.toml.
const miseVersion = (tool: string) =>
  execFileSync("mise", ["current", tool], { encoding: "utf8" }).trim();

// El tipo de instancia y su número fijan lo que el Worker cuenta como gasto
// (src/container.ts), así que se declaran aquí una sola vez y se pasan a `env`.
const INSTANCE_TYPE = "standard-2";
const INSTANCES = 2;

const runner = defineContainer({
  name: "qg-runner",
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

export default defineConfig({
  worker: {
    name: "qiskit-guides",
    compatibilityDate: "2026-10-01",
    entrypoint,
    // Workers Logs guarda solo lo que escribe src/log.ts. El registro de
    // invocaciones lleva la petición, así que está apagado.
    observability: {
      enabled: true,
      logs: { enabled: true, invocationLogs: false },
    },
    // site/ (wrangler.config.ts) se sirve desde este mismo Worker.
    // Solo las rutas de WORKER_FIRST lo invocan.
    assets: { runWorkerFirst: WORKER_FIRST },
    triggers: [triggers.scheduled({ schedule: "17 3 * * *" })],
    env: {
      // Las cuentas, el progreso y los intentos (src/schema.sql).
      DB: bindings.d1({ name: "qiskit-guides" }),
      // Los clientes OAuth se crean en las cuentas de Google y GitHub, y sus
      // secretos no se escriben aquí.
      GOOGLE_CLIENT_ID: bindings.secret(),
      GOOGLE_CLIENT_SECRET: bindings.secret(),
      GITHUB_CLIENT_ID: bindings.secret(),
      GITHUB_CLIENT_SECRET: bindings.secret(),
      AUTH_PER_MINUTE: bindings.text("10"),
      AUTH_SESSION_DAYS: bindings.text("30"),
      SIGNED_IN_IP_FACTOR: bindings.text("4"),
      ATTEMPT_RETENTION_DAYS: bindings.text("180"),
      ACCOUNT_RETENTION_DAYS: bindings.text("730"),
      // El secreto del widget de Turnstile no se escribe aquí: se crea en la cuenta.
      TURNSTILE_SECRET: bindings.secret(),
      // La clave del sitio es pública y se copia desde el widget de Turnstile.
      TURNSTILE_SITE_KEY: bindings.text("0x4AAAAAAFeMJBfEJZkBlG8m"),
      RATE_PER_MINUTE: bindings.text("30"),
      RATE_PER_DAY: bindings.text("1000"),
      MAX_CODE_BYTES: bindings.text("20000"),
      // El gasto estimado del mes no pasa de este tope. La factura de Workers
      // Paid (5 USD) no cuenta en él.
      MONTHLY_BUDGET_USD: bindings.text("2"),
      // Quien no mantiene el sitio gasta hasta esta parte del presupuesto, y de ella
      // no más de 1/PUBLIC_BUDGET_DAYS en un día. Lo demás es de los mantenedores.
      PUBLIC_BUDGET_SHARE: bindings.text("0.75"),
      PUBLIC_BUDGET_DAYS: bindings.text("15"),
      INSTANCE_TYPE: bindings.text(INSTANCE_TYPE),
      INSTANCES: bindings.text(String(INSTANCES)),
      // 10 s de trabajo, el arranque de la instancia y un reintento tras un 503.
      RESERVED_BUSY_SECONDS: bindings.text("30"),
      // Ids numéricos de GitHub, separados por comas, de quienes mantienen el sitio.
      // 20960328 es el de totallynotdavid.
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
