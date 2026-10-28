// Tests seeking inside a step: the +5 s and −5 s controls after jumping to a step.
//
//     mise run serve                              # in another terminal
//     bun tools/seektest.ts [lesson [step]]
//
// By default it uses the third step («construir») of p1-composer, a list that is revealed item by item.
import { mkdirSync } from "node:fs";
import { join, resolve } from "node:path";

import { chromium } from "playwright";

import { courseOf } from "./course";

const SHOTS = resolve(import.meta.dirname, "..", "shots");
const VISIBLE_ITEMS =
  "[...document.querySelectorAll('#scene li')].filter(li => !li.classList.contains('hid')).length";

const round = (x: number): number => Math.round(x * 100) / 100;

async function main(): Promise<void> {
  const [lesson = "p1-composer", stepText = "2"] = process.argv.slice(2);
  const step = Number(stepText);
  const url = `http://localhost:8810/${courseOf(lesson)}/lesson.html?l=${lesson}`;
  mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  const page = await browser.newPage({
    viewport: { width: 1366, height: 768 },
    colorScheme: "dark",
  });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(url);
  await page.waitForTimeout(1200);
  await page.click("#go");
  await page.waitForTimeout(2500);
  await page.locator("#steps").fill(String(step));
  await page.waitForTimeout(1500);
  await page.click("#fwd5");
  await page.waitForTimeout(1500);
  const time = await page.evaluate<number[]>(
    "[window.QGNarration.currentTime, window.QGNarration.duration]",
  );
  console.log("audio at", time.map(round));
  console.log(
    "tag:",
    await page.innerText("#tag"),
    "| visible list items:",
    await page.evaluate<number>(VISIBLE_ITEMS),
  );
  console.log("caption:", (await page.innerText("#caption")).slice(0, 80));
  await page.screenshot({ path: join(SHOTS, "seek-1.png") });
  await page.keyboard.press("Shift+ArrowLeft");
  await page.waitForTimeout(1200);
  console.log(
    "after −5 s, visible items:",
    await page.evaluate<number>(VISIBLE_ITEMS),
  );
  await page.click("#fwd5");
  await page.waitForTimeout(800);
  console.log("after +5 s, tag:", await page.innerText("#tag"));
  console.log("step:", await page.innerText("#stepno"));
  await page.goto(url);
  await page.waitForTimeout(1000);
  const resume = await page.isVisible("#resume");
  console.log(
    "resume button:",
    resume,
    resume ? await page.innerText("#resume") : "",
  );
  console.log("errors:", errors.length ? errors : "none");
  await browser.close();
}

await main();
