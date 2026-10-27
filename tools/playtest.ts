// Real playback test (with audio and timings): answers the lesson's first two
// questions (multiple-choice ones first wrong, then right) and moves on.
//     mise run serve                              # in another terminal
//     bun tools/playtest.ts [lesson]
// Uses the Chromium that `mise run install` installs and leaves screenshots in
// shots/. PLAYTEST_URL changes the server address.
import { mkdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { chromium } from "playwright";
import type { Page } from "playwright";

const ROOT = resolve(import.meta.dirname, "..");
const SHOTS = join(ROOT, "shots");

type Question =
  | { kind: "choice"; options: unknown[]; right: number }
  | { kind: "numeric"; answer: number | string };
interface Lesson {
  beats: { ask?: { kind: string } }[];
}

const isQuestion = (ask: { kind: string }): ask is Question =>
  ask.kind === "choice" || ask.kind === "numeric";

function answerable(lesson: Lesson): [number, Question][] {
  return lesson.beats.flatMap((beat, n): [number, Question][] =>
    beat.ask && isQuestion(beat.ask) ? [[n, beat.ask]] : [],
  );
}

async function answer(page: Page, n: number, ask: Question): Promise<void> {
  await page.locator("#steps").fill(String(n));
  await page.waitForSelector("#ask.on", { timeout: 60000 });
  if (ask.kind === "choice") {
    const wrong = ask.options.findIndex((_, k) => k !== ask.right);
    await page.click(`#ask .opt >> nth=${wrong}`);
    console.log(
      "wrong-answer feedback:",
      (await page.innerText("#ask .fb")).slice(0, 60),
    );
    await page.click(`#ask .opt >> nth=${ask.right}`);
  } else {
    await page.fill("#ask input", String(ask.answer));
    await page.click("#ask .numrow .primary");
  }
  console.log(
    "right-answer feedback:",
    (await page.innerText("#ask .fb")).slice(0, 60),
  );
  await page.click("#ask .next-row .primary");
  await page.waitForTimeout(1000);
}

async function main(): Promise<void> {
  const lessonId = process.argv[2] ?? "p6-panorama";
  const baseUrl = (process.env.PLAYTEST_URL ?? "http://localhost:8810").replace(
    /\/+$/,
    "",
  );
  const lesson = JSON.parse(
    readFileSync(
      join(ROOT, "site", "qiskit", "lessons", lessonId, "lesson.json"),
      "utf8",
    ),
  ) as Lesson;
  mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  const page = await browser.newPage({
    viewport: { width: 1366, height: 768 },
  });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  await page.goto(`${baseUrl}/qiskit/lesson.html?l=${lessonId}`);
  await page.waitForTimeout(1500);
  console.log("start:", await page.innerText("#start-meta"));
  await page.click("#go");
  await page.waitForTimeout(4000);
  console.log(
    "caption at t=4s:",
    (await page.innerText("#caption")).slice(0, 70),
  );
  await page.screenshot({ path: join(SHOTS, "play-1.png") });
  for (const [n, ask] of answerable(lesson).slice(0, 2)) {
    await answer(page, n, ask);
    console.log("after continuing:", await page.innerText("#tag"));
  }
  await page.screenshot({ path: join(SHOTS, "play-2.png") });
  await page.click("#next");
  await page.waitForTimeout(1500);
  const ended = await page.isVisible("#end");
  console.log(
    "end visible:",
    ended,
    "|",
    ended ? await page.innerText("#end-score") : "",
  );
  await page.screenshot({ path: join(SHOTS, "play-3.png") });
  console.log("errors:", errors.length ? errors : "none");
  await browser.close();
}

await main();
