// The shell in a browser, with Playwright on site/ served by Bun:
//     bun tests/shell_test.ts
// A first-time visitor reaches lesson 1 from the catalog, a returning one reaches the next lesson
// from the course page, the keys written before the shell move to their course once, the streak
// counts the days with XP, and the shell launches offline.
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { chromium } from "playwright";
import type { Browser, Page } from "playwright";

import { newContext, verify } from "./offline.ts";
import { serveSite } from "./site.ts";

const SITE = resolve(import.meta.dirname, "..", "site");
interface Course {
  parts: { lessons: { id: string; title: string }[] }[];
  guides?: { id: string; title: string }[];
}
const courseOf = (slug: string): Course =>
  JSON.parse(readFileSync(join(SITE, slug, "course.json"), "utf8")) as Course;
const lessonsOf = (slug: string) =>
  courseOf(slug).parts.flatMap((part) => part.lessons);

const qiskit = lessonsOf("qiskit");
const physics = lessonsOf("computational-physics");

const failures: string[] = [];
function check(ok: boolean, message: string): void {
  if (!ok) failures.push(message);
}
const same = (what: string, got: unknown, expected: unknown): void =>
  check(
    JSON.stringify(got) === JSON.stringify(expected),
    `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(got)}`,
  );

async function visitor(browser: Browser, storage: Record<string, string>) {
  // A 390 px phone: the layout this shell is made for.
  const context = await newContext(browser, {
    viewport: { width: 390, height: 844 },
    hasTouch: true,
    serviceWorkers: "block",
  });
  await context.addInitScript(
    `if (!sessionStorage.seeded) { sessionStorage.seeded = "1";
       for (const [k, v] of Object.entries(${JSON.stringify(storage)})) localStorage.setItem(k, v); }`,
  );
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  return { context, page, errors };
}

const showing = (page: Page, selector: string, text: string) =>
  page.waitForFunction(
    ([css, start]) =>
      document.querySelector(css)?.textContent?.startsWith(start),
    [selector, text],
  );
const lessonId = (page: Page) => new URL(page.url()).searchParams.get("l");
const stored = (page: Page, key: string) =>
  page.evaluate((k) => localStorage.getItem(k), key);

async function firstVisit(browser: Browser, base: string): Promise<void> {
  const { context, page, errors } = await visitor(browser, {});
  await page.goto(`${base}/`);
  same(
    "no course is filled before one is started",
    await page.locator(".btn.primary").count(),
    0,
  );
  await page.locator(".course-card .btn").first().tap();
  await page.waitForURL(/lesson\.html/);
  same("a tap on the catalog reaches lesson 1", lessonId(page), qiskit[0].id);
  await showing(page, "#start-title", qiskit[0].title);
  same("page errors", errors, []);
  await context.close();
}

async function catalogStates(browser: Browser, base: string): Promise<void> {
  const signedOut = await visitor(browser, {});
  await signedOut.page.goto(`${base}/`);
  await signedOut.page.locator("h1").waitFor();
  same(
    "signed out catalog has no friends link",
    await signedOut.page.locator('a[href="/amigos/"]').count(),
    0,
  );
  same(
    "signed out empty header has no stats",
    await signedOut.page.locator(".stats li").count(),
    0,
  );
  same(
    "signed out catalog heading",
    await signedOut.page.locator("h1").innerText(),
    "Cursos",
  );
  same("signed out page errors", signedOut.errors, []);
  await signedOut.context.close();

  const started = await visitor(browser, {
    "qiskit:done": JSON.stringify([qiskit[0].id]),
  });
  await started.page.goto(`${base}/`);
  await started.page.locator('.stats a[href="/qiskit/repaso/"]').waitFor();
  same(
    "signed out progress has a streak link without XP",
    await started.page.locator('.stats a[href="/qiskit/repaso/"]').count(),
    1,
  );
  await started.context.close();

  const signedIn = await visitor(browser, { "rising:cuenta": "account-flag" });
  await signedIn.page.goto(`${base}/`);
  await signedIn.page.locator('.stats a[href="/amigos/"]').waitFor();
  same(
    "signed in catalog has one friends link",
    await signedIn.page.locator('a[href="/amigos/"]').count(),
    1,
  );
  same(
    "signed in XP link labels friends",
    await signedIn.page
      .locator('a[href="/amigos/"]')
      .getAttribute("aria-label"),
    "0 XP hoy. Ver amigos y tablero",
  );
  await signedIn.context.close();

  const completed = await visitor(browser, {
    "qiskit:done": JSON.stringify([qiskit[0].id]),
  });
  await completed.page.goto(`${base}/`);
  await completed.page.getByRole("heading", { name: "Tus cursos" }).waitFor();
  same(
    "completed lesson catalog heading",
    await completed.page.locator("h1").innerText(),
    "Tus cursos",
  );
  same("completed lesson page errors", completed.errors, []);
  await completed.context.close();
}

async function returningVisit(browser: Browser, base: string): Promise<void> {
  const done = JSON.stringify(qiskit.slice(0, 2).map((l) => l.id));
  const { context, page, errors } = await visitor(browser, {
    "qiskit:done": done,
  });
  await page.goto(`${base}/qiskit/`);
  const current = page.locator("a[data-current]");
  await page.waitForFunction(
    (href) =>
      document.querySelector("a[data-current]")?.getAttribute("href") === href,
    `/qiskit/lesson.html?l=${qiskit[2].id}`,
  );
  same(
    "the lit node is the third lesson",
    await current.getAttribute("href"),
    `/qiskit/lesson.html?l=${qiskit[2].id}`,
  );
  await current.tap();
  await page.waitForURL(/lesson\.html/);
  same(
    "a tap on the course page reaches the next lesson",
    lessonId(page),
    qiskit[2].id,
  );

  await page.goto(`${base}/`);
  // The page paints the server's empty state first, then what the browser stored.
  await showing(page, ".btn.primary", "Continuar");
  await page.locator(".btn.primary").tap();
  await page.waitForURL(/lesson\.html/);
  same(
    "a tap on the catalog reaches the next lesson",
    lessonId(page),
    qiskit[2].id,
  );
  same("page errors", errors, []);
  await context.close();
}

async function courseOpening(browser: Browser, base: string): Promise<void> {
  const existing = qiskit[0].id;
  const guide = courseOf("qiskit").guides?.[0];
  if (!guide) throw new Error("qiskit has no guide links");
  const { context, page, errors } = await visitor(browser, {
    "qiskit:done": JSON.stringify([existing]),
  });
  await page.goto(`${base}/qiskit/`);
  await page.locator(".outcome").waitFor();
  check(
    (await page.locator(".outcome").innerText()).includes("Programa circuitos"),
    "the course opening shows its outcome",
  );
  same(
    "an expanded unit has one progress count",
    await page.locator(".unit[open] .count").count(),
    1,
  );
  same(
    "an expanded unit has no body progress",
    await page.locator(".unit[open] .unit-progress").count(),
    0,
  );
  check(
    (await page.locator(".hcur").count()) === 1 &&
      (await page.locator(".units").count()) === 1 &&
      (await page.locator(".hcur").boundingBox())!.y <
        (await page.locator(".units").boundingBox())!.y,
    "the current milestone appears above the units",
  );
  same(
    "existing lesson ids remain done",
    await page.locator(`a.node[data-state="done"]`).count(),
    1,
  );
  const guideLink = page.locator(`.guides a[href*="${guide.id}"]`);
  same("guides are unlocked links", await guideLink.count(), 1);
  await guideLink.tap();
  await page.waitForURL(new RegExp(`l=${guide.id}$`));
  same("a guide opens directly", lessonId(page), guide.id);
  same("course opening page errors", errors, []);
  await context.close();
}

async function migration(browser: Browser, base: string): Promise<void> {
  const own = qiskit[0].id;
  const foreign = physics[0].id;
  const { context, page, errors } = await visitor(browser, {
    "qiskit:done": JSON.stringify([own, foreign]),
    [`qiskit:pos:${foreign}`]: "4",
    [`qiskit:pos:${own}`]: "2",
    [`qiskit:exercise:${foreign}/solucion`]: '{"code":"x"}',
    "qiskit:theme": "dark",
    "qiskit:speed": "1.5",
  });
  await page.goto(`${base}/`);
  await page.waitForFunction(() => localStorage.getItem("rising:migrated"));
  const read = async (key: string) => stored(page, key);
  same(
    "qiskit keeps its lessons",
    await read("qiskit:done"),
    JSON.stringify([own]),
  );
  same(
    "physics receives its lessons",
    await read("computational-physics:done"),
    JSON.stringify([foreign]),
  );
  same(
    "a position moves to its course",
    await read(`computational-physics:pos:${foreign}`),
    "4",
  );
  same("the old position is gone", await read(`qiskit:pos:${foreign}`), null);
  same("a qiskit position stays", await read(`qiskit:pos:${own}`), "2");
  same(
    "an exercise moves to its course",
    await read(`computational-physics:exercise:${foreign}/solucion`),
    '{"code":"x"}',
  );
  for (const [name, value] of [
    ["theme", "dark"],
    ["speed", "1.5"],
  ])
    same(
      `the ${name} preference moves`,
      [await read(`rising:${name}`), await read(`qiskit:${name}`)],
      [value, null],
    );

  // A later load leaves what the learner wrote since alone.
  await page.evaluate(() => localStorage.setItem("qiskit:done", "[]"));
  await page.goto(`${base}/qiskit/`);
  await page.locator("a[data-current]").waitFor();
  same("it runs once", await read("qiskit:done"), "[]");
  same("page errors", errors, []);
  await context.close();
}

const days = (ago: number) => {
  const day = new Date();
  day.setDate(day.getDate() - ago);
  return [
    day.getFullYear(),
    String(day.getMonth() + 1).padStart(2, "0"),
    String(day.getDate()).padStart(2, "0"),
  ].join("-");
};
async function streak(browser: Browser, base: string): Promise<void> {
  const cases: [string, Record<string, number>, string, string][] = [
    ["nothing earned", {}, "", ""],
    ["today only", { [days(0)]: 20 }, "Racha: 1 día", "20 XP hoy"],
    [
      "yesterday keeps it alive",
      { [days(1)]: 10, [days(2)]: 10 },
      "Racha: 2 días",
      "0 XP hoy",
    ],
    [
      "a gap ends it",
      { [days(0)]: 10, [days(2)]: 10 },
      "Racha: 1 día",
      "10 XP hoy",
    ],
    ["two days ago ends it", { [days(2)]: 10 }, "Racha: 0 días", "0 XP hoy"],
  ];
  for (const [name, log, streakText, xpText] of cases) {
    const { context, page } = await visitor(browser, {
      "rising:xp": JSON.stringify(log),
    });
    await page.goto(`${base}/qiskit/`);
    const items = page.locator(".stats li");
    if (!streakText) {
      same(`${name}: stats`, await items.count(), 0);
    } else {
      await page.waitForFunction(
        (want) => document.querySelector(".stats li")?.textContent === want,
        streakText,
      );
      same(`${name}: streak`, await items.nth(0).textContent(), streakText);
      same(`${name}: xp`, await items.nth(1).textContent(), xpText);
    }
    await context.close();
  }
}

async function offline(browser: Browser, base: string): Promise<void> {
  // Playwright's routing bypasses the service worker, so this context has none.
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  await context.addInitScript(
    `localStorage.setItem("qiskit:done", ${JSON.stringify(JSON.stringify(qiskit.slice(0, 2).map((l) => l.id)))})`,
  );
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  await page.goto(`${base}/qiskit/`);
  // The worker is active once it has cached the shell, and it claims the page when it activates.
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.waitForFunction(() => navigator.serviceWorker.controller);
  const cached = await page.evaluate(async () => {
    const cache = await caches.open((await caches.keys())[0]);
    return (await cache.keys()).map((r) => new URL(r.url).pathname);
  });
  check(
    cached.includes("/qiskit/course.json"),
    "course.json of qiskit is not cached",
  );
  check(cached.includes("/courses.json"), "courses.json is not cached");
  check(
    cached.includes("/qiskit/items.json") && cached.includes("/qiskit/repaso/"),
    "the drill items or the session page are not cached",
  );
  check(
    cached.includes("/fonts/inter-latin-wght-normal.woff2") &&
      cached.includes("/fonts/inter-latin-ext-wght-normal.woff2"),
    "the Inter files are not cached",
  );
  check(
    !cached.some(
      (p) => /\.(mp3|opus|ogg|m4a|wav)$/.test(p) || p.includes("/lessons/"),
    ),
    `lesson files are cached: ${cached.filter((p) => p.includes("/lessons/"))}`,
  );

  await context.setOffline(true);
  for (const [path, heading] of [
    ["/qiskit/", "Qiskit"],
    ["/computational-physics/", "Física computacional"],
    ["/", "Tus cursos"],
  ]) {
    await page.goto(`${base}${path}`);
    same(`${path} offline`, await page.locator("h1").innerText(), heading);
  }
  // The session plays from the cache: its chunk, the scheduler and the items.
  await page.goto(`${base}/qiskit/repaso/`);
  await page.locator(".drill .prompt").waitFor();
  same("page errors", errors, []);
  await context.close();
}

const { base, stop } = serveSite();
const browser = await chromium.launch();
try {
  await firstVisit(browser, base);
  await catalogStates(browser, base);
  await returningVisit(browser, base);
  await courseOpening(browser, base);
  await migration(browser, base);
  await streak(browser, base);
  await offline(browser, base);
} finally {
  await browser.close();
  await stop();
}
verify();
for (const failure of failures) console.error(`FAIL ${failure}`);
console.log(failures.length ? `${failures.length} failures` : "shell passed");
process.exit(failures.length ? 1 : 0);
