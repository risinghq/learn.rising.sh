// The drill session in a browser, with Playwright on site/ served by Bun:
//     bun tests/session_test.ts
// Plays a session of every kind at 390 and 360 px: one miss comes back, the XP shows on the path
// page, and no screen scrolls sideways or holds a control under 3rem. A signed-in learner's XP
// waits in the queue offline and is sent when the connection returns.
// SHOTS=<directory> also writes a screenshot of every kind.
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { chromium } from "playwright";
import type { Browser, BrowserContext, Page, Route } from "playwright";

import type { Item, ItemKind } from "../drill/item.ts";
import { newContext, verify } from "./offline.ts";
import { serveSite } from "./site.ts";

const SITE = resolve(import.meta.dirname, "..", "site");
const SHOTS = process.env.SHOTS;
const KINDS: ItemKind[] = [
  "choice",
  "numeric",
  "predict",
  "parsons",
  "fill",
  "bug",
];
// A right answer first time earns 2 XP, a miss answered right when it comes back earns 1.
const EXPECTED_XP = 5 * 2 + 1;
const TAP = 48;

const failures: string[] = [];
function check(ok: boolean, message: string): void {
  if (!ok) failures.push(message);
}
const same = (what: string, got: unknown, expected: unknown): void =>
  check(
    JSON.stringify(got) === JSON.stringify(expected),
    `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(got)}`,
  );

// One item of each kind from the real bank. The prompt starts with the kind, which is how the
// test knows which screen it is on.
const bank = (
  JSON.parse(readFileSync(join(SITE, "qiskit", "items.json"), "utf8")) as {
    items: Item[];
  }
).items;
const picked = KINDS.map((kind) => {
  const item = bank.find((candidate) => candidate.kind === kind);
  if (!item) throw new Error(`the bank has no ${kind} item`);
  return { ...item, prompt: `${kind}: ${item.prompt}` } as Item;
});
const lessons = [...new Set(picked.map((item) => item.lesson))];
const ofKind = <K extends ItemKind>(kind: K) =>
  picked.find((item) => item.kind === kind) as Extract<Item, { kind: K }>;

async function visitor(
  browser: Browser,
  size: { width: number; height: number },
  storage: Record<string, string>,
): Promise<{ context: BrowserContext; page: Page; errors: string[] }> {
  const context = await newContext(browser, {
    viewport: size,
    hasTouch: true,
    serviceWorkers: "block",
  });
  await context.addInitScript(
    `if (!sessionStorage.seeded) { sessionStorage.seeded = "1";
       for (const [k, v] of Object.entries(${JSON.stringify(storage)})) localStorage.setItem(k, v); }`,
  );
  await context.route("**/qiskit/items.json", (route) =>
    route.fulfill({ json: { items: picked } }),
  );
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  return { context, page, errors };
}

const seed = { "qiskit:done": JSON.stringify(lessons) };

/** What the screen shows that a phone could not use. */
async function fit(page: Page, where: string): Promise<void> {
  const problems = await page.evaluate((tap) => {
    const out: string[] = [];
    const root = document.documentElement;
    if (root.scrollWidth > innerWidth)
      out.push(`scrolls sideways: ${root.scrollWidth} > ${innerWidth}`);
    for (const control of document.querySelectorAll(
      ".drill a, .drill button",
    )) {
      if (control.closest(".prompt, .why, .reveal")) continue;
      const box = control.getBoundingClientRect();
      if (!box.width || !box.height) continue;
      if (box.height < tap - 0.5 || box.width < tap - 0.5)
        out.push(
          `${control.className || control.tagName} is ${box.width}x${box.height}`,
        );
    }
    return out;
  }, TAP);
  same(`${where}: fit`, problems, []);
}

async function shot(page: Page, name: string): Promise<void> {
  // The verdict fades in: shoot once it has settled.
  await page.evaluate(() =>
    Promise.all(document.getAnimations().map((a) => a.finished)),
  );
  if (SHOTS) await page.screenshot({ path: join(SHOTS, `${name}.png`) });
}

const kindOnScreen = async (page: Page) => {
  const prompt = await page.locator(".prompt").first().innerText();
  return prompt.split(":")[0] as ItemKind;
};
const dock = (page: Page) => page.locator(".dock");

async function answerParsons(page: Page): Promise<void> {
  const item = ofKind("parsons");
  const place = async (line: string) => {
    const lines = await page.locator(".pool .line").allTextContents();
    await page.locator(".pool .line").nth(lines.indexOf(line)).tap();
  };
  // The first two lines go in swapped, and a drag on the first grip puts them right.
  await place(item.lines[1]!);
  await place(item.lines[0]!);
  for (const line of item.lines.slice(2)) await place(line);
  const grip = (k: number) => page.locator(".slot .grip").nth(k);
  const from = (await grip(0).boundingBox())!;
  const slot = (await page.locator(".slot").nth(1).boundingBox())!;
  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(from.x + from.width / 2, slot.y + slot.height * 0.8, {
    steps: 6,
  });
  await page.mouse.up();
  same(
    "a drag reorders the lines",
    await page.locator(".slot .line").allTextContents(),
    item.lines,
  );
  await page.getByRole("button", { name: "Comprobar" }).tap();
}

async function answerNumeric(page: Page): Promise<void> {
  const item = ofKind("numeric");
  for (const key of String(item.answer).replace(".", ","))
    await page.locator(".key", { hasText: key }).first().tap();
  await page.getByRole("button", { name: "Comprobar" }).tap();
}

/** Answers the screen right, or wrong for a choice item when `miss` is set. */
async function answer(
  page: Page,
  kind: ItemKind,
  miss: boolean,
): Promise<void> {
  switch (kind) {
    case "choice": {
      const { right, options } = ofKind("choice");
      await page
        .locator(".opt")
        .nth(miss ? (right + 1) % options.length : right)
        .tap();
      return;
    }
    case "predict":
      await page.locator(".opt").first().tap();
      return;
    case "fill":
      await page.locator(".opt").nth(ofKind("fill").right).tap();
      return;
    case "bug":
      await page.locator(".lines .line").nth(ofKind("bug").bug).tap();
      return;
    case "numeric":
      return answerNumeric(page);
    case "parsons":
      return answerParsons(page);
  }
}

/** Plays the session to its end and returns the kinds in the order they came. */
async function play(page: Page, tag: string): Promise<string[]> {
  const seen: string[] = [];
  let missed = false;
  for (;;) {
    const done = page.locator(".done");
    const prompt = page.locator(".prompt");
    await done.or(prompt.first()).waitFor();
    if (await done.count()) return seen;
    const kind = await kindOnScreen(page);
    seen.push(kind);
    await fit(page, `${tag} ${kind} asking`);
    const miss: boolean = kind === "choice" && !missed;
    await answer(page, kind, miss);
    missed ||= miss;
    await dock(page).locator(".verdict").waitFor();
    same(
      `${tag} ${kind}: verdict`,
      await dock(page).locator(".verdict").innerText(),
      kind === "predict" ? "Apuesta anotada" : miss ? "Incorrecto" : "Correcto",
    );
    check(
      (await dock(page).locator(".why").count()) === 1,
      `${tag} ${kind}: no line of why`,
    );
    if (miss)
      check(
        (await dock(page).locator(".reveal").count()) === 1,
        `${tag} ${kind}: a miss does not show the answer`,
      );
    await fit(page, `${tag} ${kind} answered`);
    await shot(page, `${tag}-${kind}${miss ? "-miss" : ""}`);
    await dock(page).getByRole("button").tap();
  }
}

async function session(browser: Browser, base: string): Promise<void> {
  for (const size of [
    { width: 390, height: 844 },
    { width: 360, height: 640 },
  ]) {
    const tag = `${size.width}x${size.height}`;
    const { context, page, errors } = await visitor(browser, size, seed);

    await page.goto(`${base}/qiskit/`);
    const card = page.locator(".review a.btn");
    await card.waitFor();
    same(
      `${tag}: the streak opens the session`,
      await page.locator(".stat a").first().getAttribute("href"),
      "/qiskit/repaso/",
    );
    await card.tap();
    await page.waitForURL(/\/qiskit\/repaso\/$/);

    const seen = await play(page, tag);
    same(
      `${tag}: every kind once, the miss again at the end`,
      [seen.slice(0, -1).toSorted(), seen.at(-1)],
      [[...KINDS].toSorted(), "choice"],
    );

    await fit(page, `${tag} done`);
    await shot(page, `${tag}-done`);
    same(
      `${tag}: xp`,
      (await page.locator(".gain").innerText()).replace(/\s+/g, " "),
      `Repaso terminado. +${EXPECTED_XP} XP`,
    );
    const keep = page.locator(".keep a");
    same(
      `${tag}: a visitor without an account may keep the streak`,
      await keep.evaluateAll((links) =>
        links.map((a) => new URL((a as HTMLAnchorElement).href).pathname),
      ),
      ["/auth/google", "/auth/github"],
    );
    const log = JSON.parse(
      (await page.evaluate(() => localStorage.getItem("qiskit:repaso")))!,
    ) as { item: string; correct: boolean }[];
    same(
      `${tag}: the log holds the first answer of each item`,
      log.map((r) => [r.item, r.correct]),
      picked.map((item) => [item.id, item.kind !== "choice"]),
    );

    await page.locator(".done .btn.primary").tap();
    await page.waitForURL(/\/qiskit\/$/);
    await page.waitForFunction(
      (want) => document.querySelectorAll(".stats li")[1]?.textContent === want,
      `${EXPECTED_XP} XP hoy`,
    );
    await page.screenshot({
      path: SHOTS ? join(SHOTS, `${tag}-path.png`) : undefined,
    });
    same(`${tag}: page errors`, errors, []);
    await context.close();
  }
}

async function signedIn(browser: Browser, base: string): Promise<void> {
  const { context, page, errors } = await visitor(
    browser,
    { width: 390, height: 844 },
    { ...seed, "rising:cuenta": "learner" },
  );
  await context.route("**/api/merge", (route) =>
    route.fulfill({
      json: {
        progress: { done: [], exercises: {}, kv: {} },
        account: "learner",
      },
    }),
  );
  const posts: Record<string, unknown>[] = [];
  let connected = false;
  await context.route("**/api/streak", (route) =>
    connected
      ? route.fulfill({ json: { current: 1, longest: 1, today: true } })
      : route.abort(),
  );
  const xp = async (route: Route) => {
    if (!connected) return route.abort();
    if (route.request().method() === "GET")
      return route.fulfill({
        json: { total: EXPECTED_XP, cap: 300, today: EXPECTED_XP },
      });
    posts.push(route.request().postDataJSON() as Record<string, unknown>);
    return route.fulfill({ json: { granted: EXPECTED_XP } });
  };
  await context.route("**/api/xp", xp);

  await page.goto(`${base}/qiskit/repaso/`);
  await play(page, "signed in");
  same(
    "signed in: no ask for an account",
    await page.locator(".keep").count(),
    0,
  );
  const queue = () =>
    page.evaluate(() =>
      JSON.parse(localStorage.getItem("rising:xpq:learner") ?? "[]"),
    );
  await page.waitForFunction(() => localStorage.getItem("rising:xpq:learner"));
  const waiting = (await queue()) as {
    ref: string;
    amount: number;
    earnedAt: number;
  }[];
  same("offline: one post waits", waiting.length, 1);
  same("offline: it carries the XP", waiting[0]?.amount, EXPECTED_XP);

  connected = true;
  await page.evaluate(() => dispatchEvent(new Event("online")));
  await page.waitForFunction(() => !localStorage.getItem("rising:xpq:learner"));
  same("online: the post is sent once", posts.length, 1);
  same("online: it is a drill post", posts[0], {
    source: "drill",
    ref: waiting[0]?.ref,
    amount: EXPECTED_XP,
    earnedAt: waiting[0]?.earnedAt,
    tz: posts[0]?.tz,
  });
  same(
    "page errors",
    errors.filter((e) => !e.includes("ERR_FAILED")),
    [],
  );
  await context.close();
}

const { base, stop } = serveSite();
const browser = await chromium.launch();
try {
  await session(browser, base);
  await signedIn(browser, base);
} finally {
  await browser.close();
  await stop();
}
verify();
for (const failure of failures) console.error(`FAIL ${failure}`);
console.log(failures.length ? `${failures.length} failures` : "session passed");
process.exit(failures.length ? 1 : 0);
