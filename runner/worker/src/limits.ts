import { type Rates, isInstanceType, ratesOf } from "./container.ts";
import type { Caps } from "./meters.ts";

export interface Env {
  TURNSTILE_SECRET: string;
  // La página recibe la clave pública en la respuesta `turnstile_missing`.
  TURNSTILE_SITE_KEY: string;
  RATE_PER_MINUTE: string;
  RATE_PER_DAY: string;
  MAX_CODE_BYTES: string;
  MONTHLY_BUDGET_USD: string;
  PUBLIC_BUDGET_SHARE: string;
  PUBLIC_BUDGET_DAYS: string;
  RESERVED_BUSY_SECONDS: string;
  INSTANCE_TYPE: string;
  INSTANCES: string;
  // Ids numéricos de GitHub separados por comas. Puede estar vacía.
  MAINTAINERS: string;
  SESSION_HOURS: string;
  AUTH_PER_MINUTE: string;
  AUTH_SESSION_DAYS: string;
  SIGNED_IN_IP_FACTOR: string;
  ATTEMPT_RETENTION_DAYS: string;
  ACCOUNT_RETENTION_DAYS: string;
  DB: D1Database;
  // Secretos de los clientes OAuth. Un proveedor sin ellos responde 503.
  GOOGLE_CLIENT_ID?: string;
  GOOGLE_CLIENT_SECRET?: string;
  GITHUB_CLIENT_ID?: string;
  GITHUB_CLIENT_SECRET?: string;
}

type NumericVar =
  | "RATE_PER_MINUTE"
  | "RATE_PER_DAY"
  | "MAX_CODE_BYTES"
  | "MONTHLY_BUDGET_USD"
  | "PUBLIC_BUDGET_SHARE"
  | "PUBLIC_BUDGET_DAYS"
  | "RESERVED_BUSY_SECONDS"
  | "INSTANCES"
  | "SESSION_HOURS"
  | "AUTH_PER_MINUTE"
  | "AUTH_SESSION_DAYS"
  | "SIGNED_IN_IP_FACTOR"
  | "ATTEMPT_RETENTION_DAYS"
  | "ACCOUNT_RETENTION_DAYS";

export interface Limits {
  perMinute: number;
  perDay: number;
  maxCodeBytes: number;
  // El cuerpo admite seis veces el código más la envoltura JSON de 1024 bytes.
  // Es el mismo tope que runner/server.py.
  maxBodyBytes: number;
  caps: Caps;
  // Lo que cuesta un segundo de instancia, según `INSTANCE_TYPE`.
  rates: Rates;
  // Instancias entre las que el Worker reparte las ejecuciones.
  instances: number;
  // El tiempo de contenedor que una ejecución aparta antes de empezar. Es un
  // tope: al llegar a `reserveMs` se detiene la instancia.
  reserveMs: number;
  // Ids de GitHub de quienes mantienen el sitio.
  maintainers: string[];
  sessionMs: number;
  // Peticiones por minuto y por IP a /auth/*.
  authPerMinute: number;
  authSessionMs: number;
  // El tope por IP de quien tiene cuenta es este múltiplo del anónimo.
  signedInIpFactor: number;
  attemptRetentionMs: number;
  accountRetentionMs: number;
}

const NANO = 1e9;
const DAY_MS = 86_400_000;

export class ConfigError extends Error {
  override name = "ConfigError";
}

function positive(env: Env, name: NumericVar, integer: boolean): number {
  const n = Number(env[name]);
  if (!Number.isFinite(n) || n <= 0 || (integer && !Number.isInteger(n))) {
    throw new ConfigError(
      `${name} debe ser un número positivo${integer ? " entero" : ""}`,
    );
  }
  return n;
}

// Un login de GitHub se puede renombrar y otra persona puede quedárselo.
// El id numérico no cambia.
function maintainerIds(list: string | undefined): string[] {
  const ids = (list ?? "")
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean);
  if (list === undefined || !ids.every((id) => /^[1-9][0-9]{0,14}$/.test(id))) {
    throw new ConfigError("MAINTAINERS debe listar ids numéricos de GitHub");
  }
  return ids;
}

// Todos los valores salen de `env` (cloudflare.config.ts); un valor ausente o
// inválido es un error de configuración, no un valor por defecto.
export function loadLimits(env: Env): Limits {
  const maxCodeBytes = positive(env, "MAX_CODE_BYTES", true);
  const budgetNano = Math.round(
    positive(env, "MONTHLY_BUDGET_USD", false) * NANO,
  );
  const share = positive(env, "PUBLIC_BUDGET_SHARE", false);
  if (share > 1) {
    throw new ConfigError("PUBLIC_BUDGET_SHARE no puede pasar de 1");
  }
  const publicNano = Math.round(budgetNano * share);
  if (!isInstanceType(env.INSTANCE_TYPE)) {
    throw new ConfigError("INSTANCE_TYPE no es un tipo de instancia conocido");
  }
  return {
    perMinute: positive(env, "RATE_PER_MINUTE", true),
    perDay: positive(env, "RATE_PER_DAY", true),
    maxCodeBytes,
    maxBodyBytes: 6 * maxCodeBytes + 1024,
    caps: {
      total: budgetNano,
      public: publicNano,
      day: Math.round(publicNano / positive(env, "PUBLIC_BUDGET_DAYS", false)),
    },
    rates: ratesOf(env.INSTANCE_TYPE),
    instances: positive(env, "INSTANCES", true),
    reserveMs: positive(env, "RESERVED_BUSY_SECONDS", false) * 1000,
    maintainers: maintainerIds(env.MAINTAINERS),
    sessionMs: positive(env, "SESSION_HOURS", false) * 3_600_000,
    authPerMinute: positive(env, "AUTH_PER_MINUTE", true),
    authSessionMs: positive(env, "AUTH_SESSION_DAYS", false) * DAY_MS,
    signedInIpFactor: positive(env, "SIGNED_IN_IP_FACTOR", true),
    attemptRetentionMs: positive(env, "ATTEMPT_RETENTION_DAYS", false) * DAY_MS,
    accountRetentionMs: positive(env, "ACCOUNT_RETENTION_DAYS", false) * DAY_MS,
  };
}
