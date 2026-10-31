// Shared theme, with Playwright on site/ served by Bun:
//     bun tests/theme_test.ts [--shots FOLDER] [--table]
// Loads the four shell pages and three lessons in each mode at 1366x768 and
// 390x844. Requires a clean console, no `#scene > .blk` outside `#stage`, one
// brand per part of the site, one font family on every page, the mode stored once, WCAG AA
// contrast and parallel lesson.json requests. --shots saves screenshots;
// --table prints the contrasts as Markdown.
import { mkdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";

import { chromium } from "playwright";
import type { Browser, BrowserContext, Page } from "playwright";

import { newContext, verify } from "./offline.ts";
import { serveSite } from "./site.ts";

const SITE = resolve(import.meta.dirname, "..", "site");
const MODES = ["dark", "light"];
const SIZES: Record<string, [number, number]> = {
  "1366x768": [1366, 768],
  "390x844": [390, 844],
};
const LESSONS = ["p1-quickstart", "p3-target", "p6-panorama"];
const SHELL: [string, string][] = [
  ["catalogo", "/"],
  ["privacidad", "/privacidad.html"],
  ["qiskit", "/qiskit/"],
  ["fisica", "/computational-physics/"],
];
// The shell draws its own button; the player pages get theme.js's.
const THEME_BUTTON = '[data-theme-ctl] button, button[aria-label^="Tema"]';
const buttonText = (page: Page): Promise<string> =>
  page
    .locator(THEME_BUTTON)
    .evaluate((b) => b.getAttribute("aria-label") ?? b.textContent ?? "");

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

type Rgb = [number, number, number];
/** The brand text and font on a page that has a brand, and the body font. */
type Brand = [string | null, string | null, string];

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
    serviceWorkers: "block",
  });
  const storage = { "rising:theme": mode, ...extraStorage };
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
  const shell = new Map<string, Brand[]>();
  const player = new Map<string, Brand[]>();
  for (const mode of MODES) {
    for (const [sizeName, size] of Object.entries(SIZES)) {
      const label = `${mode}/${sizeName}`;
      const pages: [string, string, boolean][] = SHELL.map(([name, path]) => [
        name,
        `${base}${path}`,
        true,
      ]);
      for (const id of LESSONS) {
        pages.push(
          [`${id}-b0`, `${base}/qiskit/lesson.html?l=${id}&beat=0`, false],
          [
            `${id}-bN`,
            `${base}/qiskit/lesson.html?l=${id}&beat=${lastBeats[id]}`,
            false,
          ],
        );
      }
      for (const [name, url, inShell] of pages) {
        const { context, page, errors } = await newPage(browser, size, mode);
        await page.goto(url);
        await page.waitForSelector(THEME_BUTTON);
        if (inShell) await page.waitForLoadState("networkidle");
        else await page.waitForTimeout(900);
        report.check(!errors.length, `${label} ${name}: ${errors}`);
        const attr = await page.evaluate<string | undefined>(
          "document.documentElement.dataset.theme",
        );
        report.check(attr === mode, `${label} ${name}: data-theme ${attr}`);
        if (!inShell) {
          const outside = await outsideStage(page);
          report.check(
            !outside.length,
            `${label} ${name}: blocks outside #stage ${JSON.stringify(outside)}`,
          );
        }
        const brand = await page.evaluate<Brand>(
          "(() => { const b = document.querySelector('.brand');" +
            " return [b && b.textContent.trim(), b && getComputedStyle(b).fontFamily," +
            " getComputedStyle(document.body).fontFamily]; })()",
        );
        const group = inShell ? shell : player;
        const key = `${mode}|${sizeName}`;
        group.set(key, [...(group.get(key) ?? []), brand]);
        const inter = await page.evaluate<boolean>(
          "document.fonts.ready.then(fs => [...fs].some(f => f.family.replaceAll('\"', '') === 'Inter' && f.status === 'loaded'))",
        );
        report.check(inter, `${label} ${name}: Inter did not load`);
        if (inShell) {
          const small = await page.evaluate<number>(
            "[...document.querySelectorAll('a, button, summary, input')]" +
              ".filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height && !e.closest('p, .help, footer') && (r.height < 47.5 || r.width < 47.5) && getComputedStyle(e).display !== 'inline'; }).length",
          );
          report.check(
            small === 0,
            `${label} ${name}: ${small} controls under 48 px`,
          );
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
  for (const [key, brands] of shell) {
    for (const brand of brands) {
      report.check(
        brand[0] === null || brand[0] === "Rising",
        `shell brand ${JSON.stringify(brand[0])}`,
      );
      report.check(
        brand[2] === brands[0][2] && (brand[1] ?? brand[2]) === brand[2],
        `${key}: the shell pages differ in font: ${brand.slice(1)} / ${brands[0][2]}`,
      );
    }
  }
  for (const [key, brands] of player) {
    for (const brand of brands) {
      report.check(
        brand[0] === "Qubit a qubit",
        `brand ${JSON.stringify(brand[0])}`,
      );
      report.check(
        brand[1] === brand[2] && brand[2] === shell.get(key)?.[0][2],
        `${key}: a lesson page differs in font from the shell: ${brand.slice(1)} / ${shell.get(key)?.[0][2]}`,
      );
    }
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
    await page.goto(`${base}/`);
    await page.waitForSelector(THEME_BUTTON);
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
    serviceWorkers: "block",
  });
  const page = await context.newPage();
  const theme = (): Promise<string | undefined> =>
    page.evaluate<string | undefined>("document.documentElement.dataset.theme");
  const background = (): Promise<string> =>
    page.evaluate<string>("getComputedStyle(document.body).backgroundColor");
  await page.goto(`${base}/qiskit/`);
  await page.waitForSelector(THEME_BUTTON);
  await page.waitForLoadState("networkidle");
  report.check(
    (await theme()) === undefined,
    "with no stored mode the page sets data-theme instead of following the system",
  );
  const before = await background();
  await page.click(THEME_BUTTON);
  report.check(
    (await page.evaluate<string | null>(
      "localStorage.getItem('rising:theme')",
    )) === "dark",
    "the mode button did not store the dark mode",
  );
  report.check(
    (await background()) !== before,
    "the background did not change with the mode",
  );
  report.check(
    (await buttonText(page)) === "Tema claro",
    "the shell button does not offer the other mode",
  );
  await page.goto(`${base}/qiskit/lesson.html?l=p1-quickstart&beat=0`);
  await page.waitForSelector(THEME_BUTTON);
  report.check(
    (await theme()) === "dark",
    "the player did not read the stored mode",
  );
  report.check(
    (await buttonText(page)) === "Tema claro",
    "the player button does not offer the other mode",
  );
  await page.click(THEME_BUTTON);
  await page.goto(`${base}/computational-physics/`);
  await page.waitForSelector(THEME_BUTTON);
  report.check(
    (await theme()) === "light",
    "the course page did not read the mode chosen in the player",
  );
  await context.close();
}

async function main(): Promise<void> {
  const { values } = parseArgs({
    options: { shots: { type: "string" }, table: { type: "boolean" } },
  });
  const { stop, base } = serveSite();
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
  await visit(report, browser, base, values.shots, lastBeats);
  await browser.close();
  await stop();
  verify();
  if (values.table) printTable(table);
  console.log(`${report.checks} checks, ${report.failures.length} failures`);
  for (const failure of report.failures) console.log("FAIL", failure);
  process.exit(report.failures.length ? 1 : 0);
}

await main();
