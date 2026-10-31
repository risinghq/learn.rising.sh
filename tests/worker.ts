// A local Worker with a fake identity provider, and browsers that sign in to it.
//
// `startWorker` runs `runner/worker/test/serve.ts`. `newTab` opens a browser
// whose sign-in is approved as the given provider subject, so two tabs with two
// subjects are two accounts.
import { spawn } from "node:child_process";
import type { ChildProcess } from "node:child_process";
import { join, resolve } from "node:path";

import type {
  Browser,
  BrowserContext,
  BrowserContextOptions,
  Page,
  Route,
} from "playwright";

import { newContext } from "./offline.ts";

const WORKER = join(resolve(import.meta.dirname, ".."), "runner", "worker");

// Replaces the Turnstile widget and hands over a test token.
const FAKE_TURNSTILE = `window.turnstile = {
  render(slot, o) { slot.dataset.sitekey = o.sitekey; setTimeout(() => o.callback('XXXX.DUMMY.TOKEN.XXXX'), 20); return 'w1'; },
  remove() { window.turnstileRemoved = (window.turnstileRemoved || 0) + 1; },
};`;

export type Requests = [method: string, path: string][];
export interface Tab {
  page: Page;
  context: BrowserContext;
  errors: string[];
  requests: Requests;
}

export async function call<T>(
  url: string,
  body?: Record<string, string>,
): Promise<T> {
  const response = await fetch(url, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) throw new Error(`${url} answered ${response.status}`);
  return (await response.json()) as T;
}

export async function startWorker(): Promise<{
  process: ChildProcess;
  urls: { site: string; control: string; pushHost: string };
}> {
  const child = spawn("node", ["test/serve.ts"], {
    cwd: WORKER,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let errors = "";
  child.stderr.on("data", (chunk: Buffer) => (errors += chunk));
  const line = await new Promise<string>((done) => {
    let text = "";
    child.stdout.on("data", (chunk: Buffer) => {
      text += chunk;
      if (text.includes("\n")) done(text.split("\n")[0]);
    });
    child.on("close", () => done(""));
  });
  if (!line) {
    child.kill();
    throw new Error(`the local Worker did not start: ${errors}`);
  }
  return { process: child, urls: JSON.parse(line) };
}

export async function stopWorker(worker: ChildProcess): Promise<void> {
  const exited = new Promise((done) => worker.once("exit", done));
  worker.kill("SIGTERM");
  await exited;
}

/** Answers for the identity provider: the learner approves as `subject`. A later call replaces an earlier one. */
export async function routeProvider(
  context: BrowserContext,
  control: string,
  subject: string,
): Promise<void> {
  // The Worker redirects to the provider. The browser does not follow that
  // redirect through route, so this handler answers for the provider: the
  // learner approves and returns to the redirect address with the code.
  const provider = async (route: Route): Promise<void> => {
    const response = await route.fetch({ maxRedirects: 0 });
    const authorize = response.headers()["location"];
    const { code } = await call<{ code: string }>(`${control}/consent`, {
      authorizeUrl: authorize,
      subject,
    });
    const query = new URL(authorize).searchParams;
    const back = new URLSearchParams({ code, state: query.get("state") ?? "" });
    await route.fulfill({
      response,
      headers: {
        ...response.headers(),
        location: `${query.get("redirect_uri")}?${back}`,
      },
    });
  };
  await context.route(/\/auth\/github\?/, provider);
}

export async function newTab(
  browser: Browser,
  site: string,
  control: string,
  subject: string,
  options: BrowserContextOptions = {},
): Promise<Tab> {
  const context = await newContext(browser, options);
  await context.route(
    "https://challenges.cloudflare.com/turnstile/v0/api.js*",
    (route) =>
      route.fulfill({ contentType: "text/javascript", body: FAKE_TURNSTILE }),
  );

  await routeProvider(context, control, subject);

  const page = await context.newPage();
  const errors: string[] = [];
  const requests: Requests = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("request", (r) => {
    if (r.url().startsWith(site)) {
      requests.push([r.method(), r.url().slice(site.length)]);
    }
  });
  return { page, context, errors, requests };
}
