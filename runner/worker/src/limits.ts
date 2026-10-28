import { type Rates, isInstanceType, ratesOf } from "./container.ts";
import type { Caps } from "./meters.ts";

export interface Env {
  // The Worker serves static files for the routes that are not the platform's.
  ASSETS: Fetcher;
  TURNSTILE_SECRET: string;
  // The page receives the public key in the `turnstile_missing` reply.
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
  // Numeric GitHub ids separated by commas. It may be empty.
  MAINTAINERS: string;
  SESSION_HOURS: string;
  AUTH_PER_MINUTE: string;
  AUTH_SESSION_DAYS: string;
  SIGNED_IN_IP_FACTOR: string;
  ATTEMPT_RETENTION_DAYS: string;
  ACCOUNT_RETENTION_DAYS: string;
  DB: D1Database;
  // Secrets of the OAuth clients. A provider without them answers 503.
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
  // The body allows six times the code plus the 1024-byte JSON envelope.
  // It is the same cap as runner/server.py.
  maxBodyBytes: number;
  caps: Caps;
  // What one instance second costs, according to `INSTANCE_TYPE`.
  rates: Rates;
  // Instances the Worker has: the second serves a run only while the first is busy.
  instances: number;
  // The container time that a run sets aside before it starts. It is a
  // cap: when `reserveMs` is reached the instance is stopped.
  reserveMs: number;
  // GitHub ids of the people who maintain the site.
  maintainers: string[];
  sessionMs: number;
  // Requests per minute and per IP to /auth/*.
  authPerMinute: number;
  authSessionMs: number;
  // The per-IP cap for a signed-in user is this multiple of the anonymous one.
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
      `${name} must be a positive${integer ? " integer" : " number"}`,
    );
  }
  return n;
}

// A GitHub login can be renamed and another person can take it.
// The numeric id does not change.
function maintainerIds(list: string | undefined): string[] {
  const ids = (list ?? "")
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean);
  if (list === undefined || !ids.every((id) => /^[1-9][0-9]{0,14}$/.test(id))) {
    throw new ConfigError("MAINTAINERS must list numeric GitHub ids");
  }
  return ids;
}

// Every value comes from `env` (cloudflare.config.ts); a missing or invalid
// value is a configuration error, not a default.
export function loadLimits(env: Env): Limits {
  const maxCodeBytes = positive(env, "MAX_CODE_BYTES", true);
  const budgetNano = Math.round(
    positive(env, "MONTHLY_BUDGET_USD", false) * NANO,
  );
  const share = positive(env, "PUBLIC_BUDGET_SHARE", false);
  if (share > 1) {
    throw new ConfigError("PUBLIC_BUDGET_SHARE cannot exceed 1");
  }
  const publicNano = Math.round(budgetNano * share);
  if (!isInstanceType(env.INSTANCE_TYPE)) {
    throw new ConfigError("INSTANCE_TYPE is not a known instance type");
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
