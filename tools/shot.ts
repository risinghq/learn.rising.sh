// Screenshots of a lesson at several sizes, at chosen beats.
//
//     mise run serve                              # in another terminal
//     bun tools/shot.ts <id> <beat,beat,...> [movil|laptop] [wait ms]
// Example: bun tools/shot.ts p1-quickstart 0,3,8 laptop
// Writes shots/<size>-b<beat>.png.
import { mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { chromium } from "playwright";

const SIZES: Record<string, [number, number]> = {
  movil: [390, 844],
  laptop: [1366, 768],
};

async function main(): Promise<void> {
  const [lessonId, beatList, size = "laptop", waitMs = "9000"] =
    process.argv.slice(2);
  const beats = beatList.split(",").map(Number);
  const [width, height] = SIZES[size];
  const out = resolve(import.meta.dirname, "..", "shots");
  mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  const page = await browser.newPage({ viewport: { width, height } });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  await page.goto(`http://localhost:8810/qiskit/lesson.html?l=${lessonId}`);
  await page.waitForTimeout(1200);
  await page.click("#go");
  let current = 0;
  for (const beat of beats) {
    while (current < beat) {
      await page.click("#next");
      current += 1;
    }
    await page.waitForTimeout(Number(waitMs));
    await page.screenshot({ path: join(out, `${size}-b${beat}.png`) });
  }
  console.log("errors:", errors);
  await browser.close();
}

await main();
