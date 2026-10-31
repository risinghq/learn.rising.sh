// Optional account in a browser with a local Worker and a fake provider:
//     bun tests/account_ui_test.ts
// Checks the sync between two browsers, that a review log in an old shape does not
// break it, that deleting the account keeps the
// local copy, and that without an account the runner's refusal swaps the run buttons
// for the sign-in links. Skips with a reason when Node or the Worker dependencies are missing.
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { isDeepStrictEqual } from "node:util";

import { chromium } from "playwright";
import type { Browser, BrowserContextOptions, Locator, Page } from "playwright";

import { verify } from "./offline.ts";
import {
  call,
  newTab as openTab,
  startWorker,
  stopWorker,
  type Tab,
} from "./worker.ts";

const ROOT = resolve(import.meta.dirname, "..");
const WORKER = join(ROOT, "runner", "worker");
const DESKTOP: BrowserContextOptions = {
  viewport: { width: 1280, height: 900 },
};
const LESSON = "p1-quickstart";
const EXERCISE = "p1-quickstart/ghz";
// The fake runner fails a check whose code contains FALLA.
const FAILING = "# FALLA\nprint('primer intento')\n";
const REWRITTEN = "# FALLA\nprint('desde el otro navegador')\n";
const SUBJECT = "424242";

const failures: string[] = [];

interface ExerciseRecord {
  code: string;
  checks: number;
  passed?: boolean;
  at: number;
}
type Rows = Record<string, number>;

function check(ok: boolean, message: string): void {
  if (!ok) failures.push(message);
  console.log(ok ? "✓" : "✗", message);
}

function lastBeat(lesson: string): number {
  const { beats } = JSON.parse(
    readFileSync(
      join(ROOT, "site", "qiskit", "lessons", lesson, "lesson.json"),
      "utf8",
    ),
  ) as { beats: unknown[] };
  return beats.length - 1;
}

function missionUrl(lesson: string): string {
  const { beats } = JSON.parse(
    readFileSync(
      join(ROOT, "site", "qiskit", "lessons", lesson, "lesson.json"),
      "utf8",
    ),
  ) as { beats: { id: string }[] };
  const mission = beats.findIndex((beat) => beat.id === "mision");
  return `/qiskit/lesson.html?l=${lesson}&beat=${mission}`;
}

async function openPanel(
  page: Page,
  base: string,
  lesson: string,
  k: number,
): Promise<Locator> {
  await page.goto(base + missionUrl(lesson));
  const panel = page.locator(".xpanel").nth(k);
  await panel.locator(".cm-editor").waitFor();
  return panel;
}

async function write(page: Page, panel: Locator, code: string): Promise<void> {
  await panel.locator(".cm-content").click();
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.insertText(code);
}

function unblank(code: string): string {
  return code
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => line.trimEnd())
    .join("\n");
}

async function editorText(panel: Locator): Promise<string> {
  return unblank(await panel.locator(".cm-content").innerText());
}

async function press(panel: Locator, name: string): Promise<void> {
  await panel.getByRole("button", { name }).click();
}

async function waitResult(panel: Locator, timeout = 40_000): Promise<void> {
  await panel.locator(".xstatus.ok, .xstatus.bad").waitFor({ timeout });
}

// A new browser: the Turnstile widget and the provider screen are fake.
const newTab = (
  browser: Browser,
  site: string,
  control: string,
): Promise<Tab> => openTab(browser, site, control, SUBJECT, DESKTOP);

async function stored<T>(page: Page, key: string): Promise<T | null> {
  const text = await page.evaluate<string | null, string>(
    (k) => localStorage.getItem(k),
    key,
  );
  return JSON.parse(text ?? "null") as T | null;
}

async function menu(page: Page, name: string): Promise<void> {
  await page.getByRole("button", { name, exact: true }).click();
}

async function signIn(page: Page): Promise<void> {
  await menu(page, "Entrar");
  await page
    .getByRole("button", { name: "Entrar con GitHub", exact: true })
    .click();
  await page.getByRole("button", { name: "Cuenta ✓", exact: true }).waitFor();
}

async function anonymous(
  browser: Browser,
  site: string,
  control: string,
): Promise<Tab> {
  const tab = await newTab(browser, site, control);
  const { page, requests } = tab;
  await page.goto(`${site}/qiskit/`);
  // The account button appears once the page is interactive.
  await page.locator(".acct > button").first().waitFor();
  await page.getByRole("button", { name: "Marcar como hecho" }).click();
  await page.goto(`${site}/privacidad.html`);
  const panel = await openPanel(page, site, LESSON, 1);
  await write(page, panel, FAILING);
  await press(panel, "Comprobar");
  // The Worker answers 401 and the editor swaps its run buttons for the sign-in links.
  await panel.locator(".xgate").waitFor();
  check(
    (await panel.locator(".xgate").isVisible()) &&
      (await panel.getByRole("button", { name: "Comprobar" }).isHidden()) &&
      (await panel.locator(".xtests li").count()) === 0,
    "anonymous: the runner refuses and the editor asks for an account",
  );
  await page.goto(
    `${site}/qiskit/lesson.html?l=${LESSON}&beat=${lastBeat(LESSON)}`,
  );
  await page.locator("#next").click();
  await page.locator("#end:not(.hide)").waitFor();
  check(
    isDeepStrictEqual(await stored(page, "qiskit:done"), [LESSON]),
    "anonymous: the lesson is marked done in the browser",
  );
  const record = await stored<ExerciseRecord>(
    page,
    `qiskit:exercise:${EXERCISE}`,
  );
  check(
    record !== null &&
      record.code === FAILING &&
      !record.checks &&
      !record.passed &&
      record.at > 0,
    `anonymous: the exercise stores the code and the time, with no check (${JSON.stringify(record)})`,
  );
  await page.waitForTimeout(2500);
  const ours = [
    ...new Set(
      requests
        .filter(
          ([method, path]) =>
            /^\/(api|auth|health)/.test(path) || method !== "GET",
        )
        .map(
          ([method, path]) => `${method} ${path.split("?")[0].split("#")[0]}`,
        ),
    ),
  ].toSorted();
  check(
    isDeepStrictEqual(ours, ["POST /run"]),
    `anonymous: the only own request that is not a file is the /run the Worker refused (${JSON.stringify(ours)})`,
  );
  check(
    isDeepStrictEqual(await stored(page, "qiskit:hitos"), [1]),
    "anonymous: the ticked milestone stays in the browser",
  );
  check(
    (await page.locator(".acct > button").first().innerText()) === "Entrar",
    "anonymous: the menu offers sign-in",
  );
  return tab;
}

// A browser that used the inline review keeps `{id: {box, due}}` in <course>:repaso. The account
// rejects that shape, so the page must drop it before the merge or the whole sync fails.
async function staleReview(
  browser: Browser,
  site: string,
  control: string,
): Promise<void> {
  const { page, errors } = await newTab(browser, site, control);
  await page.addInitScript(() => {
    if (sessionStorage.getItem("seeded")) return;
    sessionStorage.setItem("seeded", "1");
    localStorage.setItem(
      "qiskit:repaso",
      JSON.stringify({ "p1-quickstart-q1": { box: 2, due: 1761800000000 } }),
    );
  });
  const merged = page.waitForResponse((r) => r.url().endsWith("/api/merge"));
  await page.goto(`${site}/qiskit/`);
  await signIn(page);
  const status = (await merged).status();
  check(status === 200, `stale review: the merge succeeds (${status})`);
  check(
    (await stored(page, "qiskit:repaso")) === null,
    "stale review: the boxes of the old review are gone",
  );
  check(
    (await page.getByText("No se pudo sincronizar").count()) === 0,
    "stale review: the page reports no sync failure",
  );
  check(
    !errors.length,
    `stale review: no page errors ${JSON.stringify(errors)}`,
  );
  await page.context().close();
}

async function main(): Promise<void> {
  if (
    !Bun.which("node") ||
    !existsSync(join(WORKER, "node_modules", "miniflare"))
  ) {
    console.log("skipped: needs node and `mise run install`");
    return;
  }
  const { process: worker, urls } = await startWorker();
  const { site, control } = urls;
  try {
    const browser = await chromium.launch();
    const {
      page: one,
      errors: oneErrors,
      requests: oneRequests,
    } = await anonymous(browser, site, control);
    check(
      (await call<Rows>(`${control}/rows`)).users === 0,
      "anonymous: the server has no account",
    );

    await one.goto(
      `${site}/qiskit/lesson.html?l=${LESSON}&beat=${lastBeat(LESSON)}`,
    );
    await signIn(one);
    let rows = await call<Rows>(`${control}/rows`);
    check(
      rows.users === 1 &&
        rows.lesson_done === 1 &&
        rows.exercise_state === 1 &&
        rows.kv === 1,
      `on sign-in: the account stores the lesson, the exercise and the milestone (${JSON.stringify(rows)})`,
    );
    check(
      isDeepStrictEqual(await stored(one, "qiskit:done"), [LESSON]) &&
        (await stored<ExerciseRecord>(one, `qiskit:exercise:${EXERCISE}`))
          ?.code === FAILING,
      "on sign-in: the local copy is kept",
    );

    // Signed in, the same code runs and its failed check goes to the account.
    let panel = await openPanel(one, site, LESSON, 1);
    const checked = one.waitForResponse(
      (r) => r.url().endsWith("/api/progress") && r.status() === 204,
    );
    await press(panel, "Comprobar");
    await waitResult(panel);
    await checked;
    check(
      (await panel.locator(".xstatus.bad").count()) === 1,
      "signed in: the check runs and fails",
    );

    const { page: two, errors: twoErrors } = await newTab(
      browser,
      site,
      control,
    );
    await two.goto(`${site}/qiskit/`);
    await signIn(two);
    await two.waitForFunction(() =>
      document.querySelector(".meter .num")?.textContent?.startsWith("1 de"),
    );
    const progress = await two.locator(".meter .num").innerText();
    check(
      progress.startsWith("1 de"),
      `other browser: the course page counts the lesson as done (${progress})`,
    );
    check(
      (await two.locator(".track .hito[data-state=done]").count()) === 1,
      "other browser: the course page ticks the milestone",
    );
    panel = await openPanel(two, site, LESSON, 1);
    check(
      (await editorText(panel)) === unblank(FAILING),
      "other browser: the editor loads the code from the first one",
    );
    check(
      (await stored<ExerciseRecord>(two, `qiskit:exercise:${EXERCISE}`))
        ?.checks === 1,
      "other browser: it loads the failed check",
    );

    const saved = two.waitForResponse(
      (r) => r.url().endsWith("/api/progress") && r.status() === 204,
    );
    await write(two, panel, REWRITTEN);
    await saved;
    panel = await openPanel(one, site, LESSON, 1);
    check(
      (await editorText(panel)) === unblank(REWRITTEN),
      "on load: the most recent code of the account wins",
    );

    await staleReview(browser, site, control);

    await menu(one, "Cuenta ✓");
    await menu(one, "Borrar mi cuenta");
    await menu(one, "Sí, borrar");
    await one.getByRole("button", { name: "Entrar", exact: true }).waitFor();
    rows = await call<Rows>(`${control}/rows`);
    check(
      Object.values(rows).every((n) => n === 0),
      `delete: the server is left empty (${JSON.stringify(rows)})`,
    );
    check(
      isDeepStrictEqual(await stored(one, "qiskit:done"), [LESSON]) &&
        (await stored<ExerciseRecord>(one, `qiskit:exercise:${EXERCISE}`))
          ?.code === REWRITTEN,
      "delete: the local copy stays",
    );
    const me: unknown = await (
      await one.context().request.get(`${site}/api/me`)
    ).json();
    check(
      isDeepStrictEqual(me, { signedIn: false }),
      `delete: the session was closed (${JSON.stringify(me)})`,
    );
    const before = oneRequests.length;
    await one.reload();
    await one.locator(".xpanel").nth(1).locator(".cm-editor").waitFor();
    const after = oneRequests
      .slice(before)
      .filter(([, path]) => /^\/(api|auth)/.test(path));
    check(
      !after.length,
      `delete: the page no longer talks to the account (${JSON.stringify(after)})`,
    );

    for (const errors of [oneErrors, twoErrors]) {
      check(!errors.length, `no page errors ${JSON.stringify(errors)}`);
    }
    await browser.close();
  } finally {
    await stopWorker(worker);
  }
  verify();
  console.log(failures.length ? `\n${failures.length} failures` : "\nall good");
  process.exit(failures.length ? 1 : 0);
}

await main();
