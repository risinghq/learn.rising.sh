// Shared theme, with Playwright on site/ served by Bun:
//     bun tests/theme_test.ts [--shots FOLDER] [--table]
// Loads the front page and three lessons in each mode at 1366x768 and 390x844.
// Requires a clean console, no `#scene > .blk` outside `#stage`, one brand and
// fonts, the mode stored once, WCAG AA contrast and parallel lesson.json
// requests. --shots saves screenshots; --table prints the contrasts as Markdown.
import { mkdirSync, readFileSync } from "node:fs";
import { join, resolve, sep } from "node:path";
import { parseArgs } from "node:util";

import { chromium } from "playwright";
import type { Browser, BrowserContext, Page } from "playwright";

import { newContext, verify } from "./offline.ts";

const SITE = resolve(import.meta.dirname, "..", "site");
const MODES = ["dark", "light"];
const SIZES: Record<string, [number, number]> = {
  "1366x768": [1366, 768],
  "390x844": [390, 844],
};
const LESSONS = ["p1-quickstart", "p3-target", "p6-panorama"];

const TEXT = [
  "ink",
  "muted",
  "acc-text",
  "acc-text-hover",
  "gold",
  "red",
  "blue",
  "teal",
  "violet",
  "green",
];
const SURFACES = ["bg", "bg2", "bg3", "card", "stage"];
const GRAPHICS = ["axis", "wire", "edge"];
const LESSON_JSON_DELAY_MS = 400;

type Rgb = [number, number, number];
type Brand = [string, string, string];

// Serves site/ with a delay on every lesson.json, so that a front page that
// requests them in series takes visibly longer.
function serve(): { stop: () => Promise<void>; base: string } {
  const server = Bun.serve({
    hostname: "127.0.0.1",
    port: 0,
    async fetch(request) {
      const { pathname } = new URL(request.url);
      if (pathname.endsWith("/lesson.json")) {
        await Bun.sleep(LESSON_JSON_DELAY_MS);
      }
      const path = resolve(
        SITE,
        `.${decodeURIComponent(pathname)}${pathname.endsWith("/") ? "index.html" : ""}`,
      );
      const file = Bun.file(path);
      if (!path.startsWith(SITE + sep) || !(await file.exists())) {
        return new Response("Not found", { status: 404 });
      }
      return new Response(file);
    },
  });
  return {
    stop: () => server.stop(true),
    base: `http://127.0.0.1:${server.port}`,
  };
}

function linear(c: number): number {
  const unit = c / 255;
  return unit <= 0.03928 ? unit / 12.92 : ((unit + 0.055) / 1.055) ** 2.4;
}

function luminance([r, g, b]: Rgb): number {
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
}

function contrast(a: Rgb, b: Rgb): number {
  const [x, y] = [luminance(a), luminance(b)].toSorted((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

function parseColor(text: string): Rgb {
  const rgb = /^rgba?\(([^)]*)\)/.exec(text);
  if (rgb) {
    const [r, g, b] = rgb[1]
      .trim()
      .split(/[ ,/]+/)
      .slice(0, 3)
      .map(Number);
    return [r, g, b];
  }
  const srgb = /^color\(srgb ([^)]*)\)/.exec(text);
  if (srgb) {
    const [r, g, b] = srgb[1].split(/\s+/).slice(0, 3).map(Number);
    return [r * 255, g * 255, b * 255];
  }
  throw new Error(`cannot read the color ${text}`);
}

const RESOLVER = `names => {
  const probe = document.createElement('span');
  document.body.appendChild(probe);
  const px = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const out = {};
  for (const n of names) {
    probe.style.color = \`var(--\${n})\`;
    px.clearRect(0, 0, 1, 1);
    px.fillStyle = getComputedStyle(probe).color;
    px.fillRect(0, 0, 1, 1);
    out[n] = \`rgb(\${px.getImageData(0, 0, 1, 1).data.slice(0, 3).join(' ')})\`;
  }
  probe.remove();
  return out;
}`;

class Report {
  failures: string[] = [];
  checks = 0;

  check(ok: boolean, message: string): void {
    this.checks += 1;
    if (!ok) this.failures.push(message);
  }
}

async function newPage(
  browser: Browser,
  size: [number, number],
  mode: string,
  extraStorage: Record<string, string> = {},
): Promise<{ context: BrowserContext; page: Page; errors: string[] }> {
  const context = await newContext(browser, {
    viewport: { width: size[0], height: size[1] },
  });
  const storage = { "qiskit:theme": mode, ...extraStorage };
  await context.addInitScript(
    `for (const [k, v] of Object.entries(${JSON.stringify(storage)})) localStorage.setItem(k, v);`,
  );
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e}`));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console: ${m.text()}`);
  });
  return { context, page, errors };
}

function outsideStage(page: Page): Promise<string[]> {
  return page.evaluate<string[]>(`(() => {
    const s = document.querySelector('#stage').getBoundingClientRect();
    return [...document.querySelectorAll('#scene > .blk')].filter(b => {
      const r = b.getBoundingClientRect();
      return r.width && (r.left < s.left - 1 || r.top < s.top - 1 || r.right > s.right + 1 || r.bottom > s.bottom + 1);
    }).map(b => b.className);
  })()`);
}

async function visit(
  report: Report,
  browser: Browser,
  base: string,
  shots: string | undefined,
  lastBeats: Record<string, number>,
): Promise<void> {
  const brands = new Map<string, Brand>();
  const catalogs = new Map<string, Brand>();
  for (const mode of MODES) {
    for (const [sizeName, size] of Object.entries(SIZES)) {
      const label = `${mode}/${sizeName}`;
      const pages: [string, string][] = [
        ["catalogo", `${base}/`],
        ["index", `${base}/qiskit/index.html`],
      ];
      for (const id of LESSONS) {
        pages.push(
          [`${id}-b0`, `${base}/qiskit/lesson.html?l=${id}&beat=0`],
          [
            `${id}-bN`,
            `${base}/qiskit/lesson.html?l=${id}&beat=${lastBeats[id]}`,
          ],
        );
      }
      for (const [name, url] of pages) {
        const { context, page, errors } = await newPage(browser, size, mode);
        await page.goto(url);
        await page.waitForSelector("[data-theme-ctl] button");
        await page.waitForTimeout(name === "index" ? 1500 : 900);
        report.check(!errors.length, `${label} ${name}: ${errors}`);
        const attr = await page.evaluate<string | undefined>(
          "document.documentElement.dataset.theme",
        );
        report.check(attr === mode, `${label} ${name}: data-theme ${attr}`);
        if (name !== "index" && name !== "catalogo") {
          const outside = await outsideStage(page);
          report.check(
            !outside.length,
            `${label} ${name}: blocks outside #stage ${JSON.stringify(outside)}`,
          );
        }
        const brand = await page.evaluate<Brand>(
          "[document.querySelector('.brand').textContent.trim(), getComputedStyle(document.querySelector('.brand')).fontFamily," +
            " getComputedStyle(document.body).fontFamily]",
        );
        if (name === "catalogo") {
          catalogs.set(`${mode}|${sizeName}`, brand);
        } else {
          const key = `${mode}|${sizeName}|${name.startsWith("index")}`;
          if (!brands.has(key)) brands.set(key, brand);
        }
        if (shots) {
          const dir = join(shots, mode);
          mkdirSync(dir, { recursive: true });
          await page.screenshot({ path: join(dir, `${sizeName}-${name}.png`) });
        }
        await context.close();
      }
    }
  }
  for (const [key, value] of catalogs) {
    const course = brands.get(`${key}|true`);
    if (!course) throw new Error(`no front page was visited for ${key}`);
    report.check(
      value[0] === "Duo",
      `catalog brand ${JSON.stringify(value[0])}`,
    );
    report.check(
      value[1] === course[1] && value[2] === course[2],
      `the catalog fonts differ from the course fonts: ${value.slice(1)} / ${course.slice(1)}`,
    );
  }
  for (const [key, value] of brands) {
    const [mode, sizeName, isIndex] = key.split("|");
    const other = brands.get(`${mode}|${sizeName}|${isIndex === "false"}`);
    if (!other) throw new Error(`no counterpart was visited for ${key}`);
    report.check(
      value[0] === "Qubit a qubit",
      `brand ${JSON.stringify(value[0])}`,
    );
    report.check(
      value[1] === other[1],
      `the brand font differs between pages: ${value[1]} / ${other[1]}`,
    );
  }
}

async function contrasts(
  report: Report,
  browser: Browser,
  base: string,
): Promise<Map<string, number>> {
  const table = new Map<string, number>();
  for (const mode of MODES) {
    const { context, page } = await newPage(browser, [1366, 768], mode);
    await page.goto(`${base}/qiskit/index.html`);
    await page.waitForSelector("[data-theme-ctl] button");
    const names = [
      ...new Set([...TEXT, ...SURFACES, ...GRAPHICS, "acc-ink", "acc"]),
    ].toSorted();
    const resolved = await page.evaluate<Record<string, string>>(
      `(${RESOLVER})(${JSON.stringify(names)})`,
    );
    const colors = Object.fromEntries(
      Object.entries(resolved).map(([name, text]) => [name, parseColor(text)]),
    );
    await context.close();
    const worst = (token: string): number =>
      Math.min(
        ...SURFACES.map((surface) => contrast(colors[token], colors[surface])),
      );
    for (const token of TEXT) {
      const value = worst(token);
      table.set(`${token}|${mode}`, value);
      report.check(
        value >= 4.5,
        `contrast ${token} in ${mode}: ${value.toFixed(2)} < 4.5`,
      );
    }
    for (const token of GRAPHICS) {
      const value = worst(token);
      table.set(`${token}|${mode}`, value);
      report.check(
        value >= 3,
        `contrast ${token} in ${mode}: ${value.toFixed(2)} < 3`,
      );
    }
    const accent = contrast(colors["acc-ink"], colors.acc);
    table.set(`acc-ink/acc|${mode}`, accent);
    report.check(
      accent >= 4.5,
      `contrast acc-ink on acc in ${mode}: ${accent.toFixed(2)} < 4.5`,
    );
  }
  return table;
}

function printTable(table: Map<string, number>): void {
  const rows = [...TEXT, "acc-ink/acc", ...GRAPHICS];
  console.log(`| token | ${MODES.join(" | ")} |`);
  console.log(`| --- | ${MODES.map(() => "---:").join(" | ")} |`);
  for (const row of rows) {
    const cells = MODES.map((mode) => table.get(`${row}|${mode}`)?.toFixed(2));
    console.log(`| \`${row}\` | ${cells.join(" | ")} |`);
  }
}

async function modeStoredOnce(
  report: Report,
  browser: Browser,
  base: string,
): Promise<void> {
  const context = await newContext(browser, {
    viewport: { width: 1366, height: 768 },
    colorScheme: "light",
  });
  const page = await context.newPage();
  const theme = (): Promise<string | undefined> =>
    page.evaluate<string | undefined>("document.documentElement.dataset.theme");
  const background = (): Promise<string> =>
    page.evaluate<string>("getComputedStyle(document.body).backgroundColor");
  await page.goto(`${base}/qiskit/index.html`);
  await page.waitForSelector("[data-theme-ctl] button");
  report.check(
    (await theme()) === undefined,
    "with no stored mode the page sets data-theme instead of following the system",
  );
  const before = await background();
  await page.click("[data-theme-ctl] button");
  report.check(
    (await page.evaluate<string | null>(
      "localStorage.getItem('qiskit:theme')",
    )) === "dark",
    "the mode button did not store the dark mode",
  );
  report.check(
    (await background()) !== before,
    "the background did not change with the mode",
  );
  await page.goto(`${base}/qiskit/lesson.html?l=p1-quickstart&beat=0`);
  await page.waitForSelector("[data-theme-ctl] button");
  report.check(
    (await theme()) === "dark",
    "the player did not read the stored mode",
  );
  report.check(
    (await page.innerText("[data-theme-ctl] button")) === "Tema claro",
    "the player button does not offer the other mode",
  );
  await page.click("[data-theme-ctl] button");
  await page.goto(`${base}/qiskit/index.html`);
  await page.waitForSelector("[data-theme-ctl] button");
  report.check(
    (await theme()) === "light",
    "the front page did not read the mode chosen in the player",
  );
  await context.close();
}

async function reviewInParallel(
  report: Report,
  browser: Browser,
  base: string,
): Promise<number> {
  const done = JSON.stringify([
    "p1-quickstart",
    "p1-instalar",
    "p1-composer",
    "p1-patrones",
    "p3-target",
    "p6-panorama",
  ]);
  const { context, page, errors } = await newPage(
    browser,
    [1366, 768],
    "dark",
    { "qiskit:done": done },
  );
  const start = performance.now();
  await page.goto(`${base}/qiskit/index.html`);
  await page.waitForSelector("#repaso .rq", { timeout: 15000 });
  const seconds = (performance.now() - start) / 1000;
  const lessons = (JSON.parse(done) as string[]).length;
  const delay = LESSON_JSON_DELAY_MS / 1000;
  report.check(
    seconds < delay * (lessons - 1),
    `the review took ${seconds.toFixed(2)} s with ${lessons} lessons of ${delay} s: it requests in series`,
  );
  report.check(!errors.length, `review: ${errors}`);
  await context.close();
  return seconds;
}

async function main(): Promise<void> {
  const { values } = parseArgs({
    options: { shots: { type: "string" }, table: { type: "boolean" } },
  });
  const { stop, base } = serve();
  const lastBeats = Object.fromEntries(
    LESSONS.map((id) => {
      const lesson = JSON.parse(
        readFileSync(
          join(SITE, "qiskit", "lessons", id, "lesson.json"),
          "utf8",
        ),
      ) as { beats: unknown[] };
      return [id, lesson.beats.length - 1];
    }),
  );
  const report = new Report();
  const browser = await chromium.launch({
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  const table = await contrasts(report, browser, base);
  await modeStoredOnce(report, browser, base);
  const seconds = await reviewInParallel(report, browser, base);
  await visit(report, browser, base, values.shots, lastBeats);
  await browser.close();
  await stop();
  verify();
  if (values.table) printTable(table);
  console.log(
    `review with 6 lessons of ${LESSON_JSON_DELAY_MS / 1000} s each: ${seconds.toFixed(2)} s`,
  );
  console.log(`${report.checks} checks, ${report.failures.length} failures`);
  for (const failure of report.failures) console.log("FAIL", failure);
  process.exit(report.failures.length ? 1 : 0);
}

await main();
