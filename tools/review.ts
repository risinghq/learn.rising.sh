// Visual review: captures the final state of each beat (?beat=N mode) and builds contact sheets.
//
//     mise run serve                              # in another terminal
//     bun tools/review.ts [lesson ...] [--port 8810] [--course qiskit]
// Without lessons it reviews every lesson of --course.
// Output: shots/<lesson>/NN-<beat>-land.png, NN-<beat>-port.png and shots/<lesson>-hoja-{land,port}.png
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { parseArgs } from "node:util";

import { chromium } from "playwright";
import type { Browser, Page } from "playwright";

import { courseOf, lessonDir } from "./course";

const ROOT = resolve(import.meta.dirname, "..");
const OUT = join(ROOT, "shots");
const SIZES: Record<string, [number, number]> = {
  land: [1366, 768],
  port: [390, 844],
};
const LABEL = 22;

const OVERFLOW = `(() => { const st = document.querySelector('#stage').getBoundingClientRect();
  const tag = document.querySelector('#tag').getBoundingClientRect();
  return [...document.querySelectorAll('#scene > .blk')].some(b => { const r = b.getBoundingClientRect();
    return r.height && (r.top < tag.bottom - 2 || r.bottom > st.bottom + 1 || r.left < st.left - 1 || r.right > st.right + 1); }); })()`;

interface Lesson {
  beats: { id: string }[];
}

const readJson = <T>(path: string): T =>
  JSON.parse(readFileSync(path, "utf8")) as T;

function watch(page: Page, errors: Record<string, string[]>, id: string): void {
  const note = (message: string): void => {
    (errors[id] ??= []).push(message);
  };
  page.on("pageerror", (e) => note(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") note(m.text());
  });
}

async function sheet(
  browser: Browser,
  files: string[],
  size: [number, number],
  dest: string,
  cols: number,
): Promise<void> {
  const [width, height] = size;
  const scale = width > 1000 ? 0.5 : 0.6;
  const cellW = Math.trunc(width * scale);
  const cellH = Math.trunc(height * scale);
  const rows = Math.ceil(files.length / cols);
  const cells = files.map((file, k) => {
    const x = (k % cols) * cellW;
    const y = Math.trunc(k / cols) * (cellH + LABEL);
    const data = readFileSync(file).toString("base64");
    return (
      `<figure style="left:${x}px;top:${y}px"><figcaption>${basename(file, ".png")}</figcaption>` +
      `<img src="data:image/png;base64,${data}" width="${cellW}" height="${cellH}"></figure>`
    );
  });
  const page = await browser.newPage({
    viewport: { width: cols * cellW, height: rows * (cellH + LABEL) },
  });
  await page.setContent(
    `<style>
      body { margin: 0; background: white; }
      figure { position: absolute; margin: 0; }
      figcaption { height: ${LABEL}px; box-sizing: border-box; padding: 4px 6px; font: 11px monospace; color: black; }
      img { display: block; }
    </style>${cells.join("")}`,
  );
  await page.evaluate(
    "Promise.all([...document.images].map((i) => i.decode()))",
  );
  await page.screenshot({ path: dest });
  await page.close();
}

async function main(): Promise<void> {
  const { values, positionals } = parseArgs({
    options: {
      port: { type: "string", default: "8810" },
      course: { type: "string", default: "qiskit" },
    },
    allowPositionals: true,
  });
  const ids = positionals.length
    ? positionals
    : readJson<{ parts: { lessons: { id: string }[] }[] }>(
        join(ROOT, "site", values.course, "course.json"),
      ).parts.flatMap((part) => part.lessons.map((lesson) => lesson.id));
  const errors: Record<string, string[]> = {};
  const browser = await chromium.launch();
  for (const id of ids) {
    const course = courseOf(id);
    const dir = lessonDir(id);
    const lesson = readJson<Lesson>(join(dir, "lesson.json"));
    if (!existsSync(join(dir, "timings.json"))) {
      console.log(id, "has no timings, skipped");
      continue;
    }
    mkdirSync(join(OUT, id), { recursive: true });
    for (const [tag, size] of Object.entries(SIZES)) {
      const page = await browser.newPage({
        viewport: { width: size[0], height: size[1] },
      });
      watch(page, errors, id);
      const files: string[] = [];
      for (const [n, beat] of lesson.beats.entries()) {
        await page.goto(
          `http://localhost:${values.port}/${course}/lesson.html?l=${id}&beat=${n}`,
        );
        await page.waitForTimeout(1700);
        const name = `${String(n).padStart(2, "0")}-${beat.id}-${tag}`;
        const file = join(OUT, id, `${name}.png`);
        await page.screenshot({ path: file });
        files.push(file);
        if (await page.evaluate<boolean>(OVERFLOW)) {
          (errors[id] ??= []).push(`overflow in ${name}`);
        }
      }
      await page.close();
      await sheet(
        browser,
        files,
        size,
        join(OUT, `${id}-hoja-${tag}.png`),
        tag === "land" ? 3 : 6,
      );
    }
    console.log(id, "ok");
  }
  await browser.close();
  console.log(
    "errors:",
    Object.keys(errors).length ? JSON.stringify(errors, null, 1) : "none",
  );
}

await main();
