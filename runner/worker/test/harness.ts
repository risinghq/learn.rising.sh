import { readFileSync } from "node:fs";
import http from "node:http";
import path from "node:path";

import { build } from "esbuild";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";

import { WORKER_FIRST } from "../src/routes.ts";
import { CLIENTS, FakeProvider } from "./provider.ts";

// Test secrets that Cloudflare documents for Turnstile.
export const PASS_SECRET = "1x0000000000000000000000000000000AA";
export const FAIL_SECRET = "2x0000000000000000000000000000000AA";
export const SPENT_SECRET = "3x0000000000000000000000000000000AA";

export const HOME_HOST = "edu.example.test";

export const VARS = {
  TURNSTILE_SECRET: PASS_SECRET,
  TURNSTILE_SITE_KEY: "1x00000000000000000000AA",
  RATE_PER_MINUTE: "1000",
  RATE_PER_DAY: "100000",
  MAX_CODE_BYTES: "20000",
  MONTHLY_BUDGET_USD: "1000",
  PUBLIC_BUDGET_SHARE: "0.75",
  PUBLIC_BUDGET_DAYS: "1",
  INSTANCE_TYPE: "standard-2",
  INSTANCES: "2",
  RESERVED_BUSY_SECONDS: "30",
  MAINTAINERS: "",
  SESSION_HOURS: "8",
  AUTH_PER_MINUTE: "1000",
  AUTH_SESSION_DAYS: "30",
  SIGNED_IN_IP_FACTOR: "4",
  ATTEMPT_RETENTION_DAYS: "180",
  ACCOUNT_RETENTION_DAYS: "730",
  GOOGLE_CLIENT_ID: CLIENTS.google.id,
  GOOGLE_CLIENT_SECRET: CLIENTS.google.secret,
  GITHUB_CLIENT_ID: CLIENTS.github.id,
  GITHUB_CLIENT_SECRET: CLIENTS.github.secret,
};

export const TOKEN = "XXXX.DUMMY.TOKEN.XXXX";

let bundle: Promise<string> | undefined;

function bundled(): Promise<string> {
  bundle ??= build({
    entryPoints: [path.join(import.meta.dirname, "entry.ts")],
    bundle: true,
    format: "esm",
    platform: "neutral",
    mainFields: ["module", "main"],
    conditions: ["workerd", "worker"],
    external: ["cloudflare:*"],
    write: false,
    logLevel: "silent",
  }).then((result) => result.outputFiles[0].text);
  return bundle;
}

export interface Reply {
  status: number;
  headers: Headers;
  body: any;
}

export interface Siteverify {
  // Key-value pairs sent to the verification service.
  calls: Record<string, string>[];
}

export interface Harness {
  post(
    body: unknown,
    options?: { ip?: string; headers?: Record<string, string>; raw?: string },
  ): Promise<Reply>;
  get(pathname: string): Promise<Reply>;
  request(
    method: string,
    pathname: string,
    options?: {
      ip?: string;
      headers?: Record<string, string>;
      body?: unknown;
      // The host of the URL. Defaults to runner.test.
      host?: string;
    },
  ): Promise<Reply>;
  // Sends only the headers of a request that declares `length` bytes of body
  // and returns the response status, without sending the body.
  declare(
    method: string,
    pathname: string,
    length: number,
    headers?: Record<string, string>,
  ): Promise<number>;
  provider: FakeProvider;
  db: D1Database;
  // HTTP origin of the Worker, for a browser.
  origin(): Promise<string>;
  purge(at?: Date): Promise<void>;
  // Lines the Worker wrote to Workers Logs.
  workerLogs(): string[];
  runnerCalls(): { path: string; headers: string[]; instance: string }[];
  // How many times the Worker stopped an instance.
  runnerStops(): number;
  // Advances by `ms` the stopped clock set by the `FAKE_CLOCK` option.
  advance(ms: number): Promise<void>;
  siteverify: Siteverify;
  dispose(): Promise<void>;
}

// Simula siteverify: 1x pasa, 2x falla, 3x indica un token usado y `down` no
// responde.
function fakeSiteverify(siteverify: Siteverify, down: boolean) {
  return async (request: Request): Promise<Response> => {
    const form = new URLSearchParams(await request.text());
    siteverify.calls.push(Object.fromEntries(form));
    if (down) return new Response("down", { status: 502 });
    const secret = form.get("secret") ?? "";
    if (secret.startsWith("1x"))
      return Response.json({ success: true, "error-codes": [] });
    const code = secret.startsWith("3x")
      ? "timeout-or-duplicate"
      : "invalid-input-response";
    return Response.json({ success: false, "error-codes": [code] });
  };
}

export interface Options {
  // FAKE_SETTLE_FAILS makes the budget adjustment fail and FAKE_CLOCK stops the
  // clock (test/entry.ts).
  vars?: Partial<typeof VARS> & {
    FAKE_SETTLE_FAILS?: string;
    FAKE_CLOCK?: string;
  };
  // Without this the Worker calls the real Turnstile service.
  siteverify?: "fake" | "down" | "real";
}

const SCHEMA = readFileSync(
  path.join(import.meta.dirname, "../src/schema.sql"),
  "utf8",
)
  .replace(/^--.*$/gm, "")
  .split(";")
  .map((statement) => statement.trim())
  .filter(Boolean);

export async function start(options: Options = {}): Promise<Harness> {
  const logs: string[] = [];
  const siteverify: Siteverify = { calls: [] };
  const provider = new FakeProvider();
  const verify = fakeSiteverify(
    siteverify,
    (options.siteverify ?? "fake") === "down",
  );
  const mode = options.siteverify ?? "fake";
  const mf = new Miniflare(
    convertV4MiniflareOptions({
      modules: true,
      script: await bundled(),
      scriptPath: path.join(process.cwd(), "worker.mjs"),
      compatibilityDate: "2026-10-01",
      bindings: { ...VARS, ...options.vars },
      // Serves site/ without invoking the Worker, except on the WORKER_FIRST routes.
      assets: {
        binding: "ASSETS",
        directory: path.join(import.meta.dirname, "../../../site"),
        run_worker_first: WORKER_FIRST,
        routerConfig: { has_user_worker: true },
      },
      durableObjects: {
        Runner: { className: "Runner", useSQLite: true },
        RateLimiter: { className: "RateLimiter", useSQLite: true },
        Budget: { className: "Budget", useSQLite: true },
      },
      d1Databases: { DB: "test-db" },
      ...(mode === "real"
        ? {}
        : {
            outboundService: (request: Request) =>
              provider.owns(new URL(request.url))
                ? provider.handle(request)
                : verify(request),
          }),
      handleStructuredLogs: (log: { message: string }) =>
        logs.push(log.message),
      logRequests: false,
    }),
  );
  const reply = async (
    response: Awaited<ReturnType<Miniflare["dispatchFetch"]>>,
  ): Promise<Reply> => {
    const text = await response.text();
    let body: any = text;
    try {
      body = JSON.parse(text);
    } catch {}
    return {
      status: response.status,
      headers: response.headers as unknown as Headers,
      body,
    };
  };
  const db = await mf.getD1Database("DB");
  for (const statement of SCHEMA) await db.prepare(statement).run();
  return {
    siteverify,
    provider,
    db,
    origin: async () => (await mf.ready).origin,
    purge: async (at = new Date()) => {
      await (await mf.getWorker()).scheduled({ scheduledTime: at });
    },
    request: async (
      method,
      pathname,
      { ip = "198.51.100.7", headers = {}, body, host = "runner.test" } = {},
    ) =>
      reply(
        await mf.dispatchFetch(`http://${host}${pathname}`, {
          method,
          redirect: "manual",
          headers: {
            "cf-connecting-ip": ip,
            ...(body === undefined
              ? {}
              : { "content-type": "application/json" }),
            ...headers,
          },
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        }),
      ),
    post: async (body, { ip = "198.51.100.7", headers = {}, raw } = {}) =>
      reply(
        await mf.dispatchFetch("http://runner.test/run", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "cf-connecting-ip": ip,
            ...headers,
          },
          body: raw ?? JSON.stringify(body),
        }),
      ),
    declare: async (method, pathname, length, headers = {}) => {
      const url = await mf.ready;
      return new Promise<number>((resolve, reject) => {
        const req = http.request(
          {
            host: url.hostname,
            port: url.port,
            method,
            path: pathname,
            headers: {
              host: "runner.test",
              "cf-connecting-ip": "198.51.100.7",
              ...headers,
              "content-length": length,
            },
          },
          (res) => {
            res.resume();
            resolve(res.statusCode ?? 0);
            req.destroy();
          },
        );
        req.on("error", reject);
        req.flushHeaders();
      });
    },
    get: async (pathname) =>
      reply(await mf.dispatchFetch(`http://runner.test${pathname}`)),
    workerLogs: () => logs.filter((line) => !line.startsWith("FAKE_RUNNER_")),
    runnerStops: () =>
      logs.filter((line) => line === "FAKE_RUNNER_STOP").length,
    advance: async (ms) => {
      await mf.dispatchFetch(`http://runner.test/clock?advance=${ms}`);
    },
    runnerCalls: () =>
      logs
        .filter((line) => line.startsWith("FAKE_RUNNER_CALL"))
        .map((line) => JSON.parse(line.slice("FAKE_RUNNER_CALL ".length))),
    dispose: () => mf.dispose(),
  };
}

// A per-minute limit counts clock windows. If less than `ms` remains before the
// window ends, wait for the next one so the test does not cross it.
export async function clearOfMinuteEnd(ms = 8000): Promise<void> {
  const left = 60_000 - (Date.now() % 60_000);
  if (left < ms) await new Promise((resolve) => setTimeout(resolve, left + 50));
}
