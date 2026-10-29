import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { chromium } from "playwright";
import type { Locator, Page } from "playwright";

import { newContext, verify } from "./offline.ts";
import { serveSite } from "./site.ts";

const COURSE_DIR = resolve(import.meta.dirname, "..", "site", "qiskit");
const POLL_MS = 10;
const WAIT_MS = 5_000;
const NARRATION_WAIT_MS = 20_000;
interface Ask {
  kind: string;
  right?: number;
}
interface Beat {
  id: string;
  ask?: Ask;
}
interface Lesson {
  title: string;
  next?: string;
  beats: Beat[];
}
interface Mission {
  notebook: string;
  tasks: number;
}
interface CourseLesson {
  id: string;
  section: string;
  title: string;
  minutes: number;
  missions?: Mission[];
}
interface Course {
  parts: { lessons: CourseLesson[] }[];
}

const course: Course = JSON.parse(
  readFileSync(join(COURSE_DIR, "course.json"), "utf8"),
);
const lessons = course.parts.flatMap((part) => part.lessons);
const lessonData = new Map<string, Lesson>();
function lessonOf(id: string): Lesson {
  let lesson = lessonData.get(id);
  if (!lesson) {
    lesson = JSON.parse(
      readFileSync(join(COURSE_DIR, "lessons", id, "lesson.json"), "utf8"),
    ) as Lesson;
    lessonData.set(id, lesson);
  }
  return lesson;
}
const reviewable = (id: string) =>
  lessonOf(id).beats.filter(
    (b) => b.ask && ["choice", "numeric"].includes(b.ask.kind),
  ).length;
const courseMissions = (lesson: CourseLesson) =>
  (lesson.missions ?? []).filter((m) => !m.notebook.includes("proyecto/"));

const done = new Set<string>();
let missionsMarked = 0;
let reviewsAnswered = 0;

let stepNo = 0;
async function step(name: string, run: () => Promise<void>): Promise<void> {
  stepNo += 1;
  const started = Date.now();
  try {
    await run();
  } catch (error) {
    console.log(`✗ step ${stepNo}: ${name}`);
    throw error;
  }
  const seconds = ((Date.now() - started) / 1000).toFixed(1);
  console.log(`✓ step ${stepNo}: ${name} (${seconds} s)`);
}

async function see(
  what: string,
  read: () => Promise<string>,
  expected: string | RegExp,
  timeout = WAIT_MS,
): Promise<void> {
  const matches = (text: string) =>
    typeof expected === "string" ? text === expected : expected.test(text);
  const deadline = Date.now() + timeout;
  let text = "";
  for (;;) {
    text = await read().catch((error: Error) => `<${error.message}>`);
    if (matches(text)) return;
    if (Date.now() > deadline) break;
    await Bun.sleep(POLL_MS);
  }
  throw new Error(`${what}: expected ${expected}, the page shows "${text}"`);
}

const text = (locator: Locator) => () => locator.innerText({ timeout: 1_000 });

async function same<T>(what: string, got: T, expected: T): Promise<void> {
  if (JSON.stringify(got) !== JSON.stringify(expected)) {
    throw new Error(
      `${what}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(got)}`,
    );
  }
}

async function openHome(page: Page, base: string): Promise<void> {
  await page.goto(`${base}/qiskit/`);
  await see(
    "progress line",
    text(page.locator("#prog")),
    /lecciones completadas/,
  );
}

async function checkProgress(page: Page): Promise<void> {
  const total = lessons.length;
  await see(
    "progress line",
    text(page.locator("#prog")),
    `${done.size}/${total} lecciones completadas`,
  );
  await same(
    "progress bar",
    await page
      .locator("#bar")
      .evaluate((bar: HTMLProgressElement) => [bar.value, bar.max]),
    [done.size, total],
  );
  const shown = await page.locator("#parts .part").evaluateAll((cards) =>
    cards.map((card) => ({
      badge: card.querySelector(".n")?.textContent,
      rows: [...card.querySelectorAll<HTMLAnchorElement>("a")].map((a) => [
        new URL(a.href).searchParams.get("l"),
        a.classList.contains("done"),
        a.querySelector(".m")?.textContent,
      ]),
    })),
  );
  const expected = course.parts.map((part) => ({
    badge: `${part.lessons.filter((l) => done.has(l.id)).length}/${part.lessons.length}`,
    rows: part.lessons.map((l) => [
      l.id,
      done.has(l.id),
      done.has(l.id) ? "Hecha" : `${l.minutes} min`,
    ]),
  }));
  await same("parts and lessons", shown, expected);
}

async function checkNext(page: Page): Promise<void> {
  const card = page.locator("#next");
  const doneInOrder = lessons.filter((l) => done.has(l.id));
  const queue = doneInOrder
    .flatMap((l) => courseMissions(l).map((m) => ({ l, m })))
    .slice(missionsMarked);
  if (queue.length) {
    const { l, m } = queue[0];
    await see(
      "next card",
      text(card.locator(".k")),
      "Tu turno: misión pendiente",
    );
    await see(
      "next card title",
      text(card.locator(".t")),
      `${l.section} ${l.title}`,
    );
    await see(
      "next card detail",
      text(card.locator(".s")),
      new RegExp(
        `^${m.tasks === 1 ? "1 misión" : `${m.tasks} misiones`} en el cuaderno`,
      ),
    );
    await see(
      "next card command",
      text(card.locator("code")),
      `uv run marimo edit ${m.notebook}`,
    );
    return;
  }
  const target = lessons.find((l) => !done.has(l.id)) ?? lessons[0];
  await see(
    "next card",
    text(card.locator(".k")),
    done.size ? "Continúa donde lo dejaste" : "Empieza aquí",
  );
  await see(
    "next card title",
    text(card.locator(".t")),
    `${target.section} ${target.title}`,
  );
  await see(
    "next card button",
    text(card.locator("a.go")),
    `${done.size ? "Continuar" : "Empezar"} la lección, ${target.minutes} min`,
  );
  await same(
    "next card link",
    await card.locator("a.go").getAttribute("href"),
    `lesson.html?l=${target.id}`,
  );
}

async function checkReview(page: Page): Promise<void> {
  const pool = lessons
    .filter((l) => done.has(l.id))
    .reduce((n, l) => n + reviewable(l.id), 0);
  const pending = pool - reviewsAnswered;
  if (!done.size) {
    await see(
      "review",
      text(page.locator("#repaso")),
      /^Cuando completes tu primera lección/,
    );
    return;
  }
  if (!pending) {
    await see(
      "review",
      text(page.locator("#repaso")),
      "Nada que repasar hoy. Vuelve mañana.",
    );
    await see("review count", text(page.locator("#rnote")), "");
    return;
  }
  await see(
    "review count",
    text(page.locator("#rnote")),
    `${Math.min(3, pending)} de ${pending} pendientes`,
  );
  await same(
    "review questions",
    await page.locator("#repaso .rq").count(),
    Math.min(3, pending),
  );
}

async function checkHome(page: Page): Promise<void> {
  await checkProgress(page);
  await checkNext(page);
  await checkReview(page);
}

const stepLabel = (page: Page) => text(page.locator("#stepno"));

async function checkStep(page: Page, n: number, total: number): Promise<void> {
  await see("step", stepLabel(page), new RegExp(`^Paso ${n} de ${total}(,|$)`));
}

async function next(page: Page, n: number, total: number): Promise<void> {
  await page.locator("#next").click();
  await checkStep(page, n, total);
}

async function answer(
  page: Page,
  id: string,
  beat: number,
  wrongFirst: boolean,
) {
  const ask = lessonOf(id).beats[beat].ask!;
  await page.locator("#ask.on").waitFor({ timeout: NARRATION_WAIT_MS });
  const options = page.locator("#ask .opt");
  if (wrongFirst) {
    const wrong = ask.right === 0 ? 1 : 0;
    await options.nth(wrong).click();
    await see("feedback of a miss", text(page.locator("#ask .fb")), /\S/);
    await same(
      "a miss has no continue button",
      await page.locator("#ask .next-row .primary").count(),
      0,
    );
    await same(
      "wrong option",
      await options.nth(wrong).evaluate((o) => o.classList.contains("wrong")),
      true,
    );
  }
  await options.nth(ask.right!).click();
  await same(
    "right option",
    await options
      .nth(ask.right!)
      .evaluate((o) => o.classList.contains("right")),
    true,
  );
  await see(
    "continue button",
    text(page.locator("#ask .next-row .primary")),
    "Continuar",
  );
}

async function playToEnd(
  page: Page,
  from: number,
  total: number,
): Promise<void> {
  for (let n = from + 1; n <= total; n++) await next(page, n, total);
  await page.locator("#next").click();
  await see(
    "end card",
    text(page.locator("#end .kicker")),
    "Lección completada",
  );
}

async function finishLesson(page: Page, id: string): Promise<void> {
  const lesson = lessonOf(id);
  await see("end title", text(page.locator("#end-title")), lesson.title);
  const nextLink = page.locator("#end-next");
  if (lesson.next) {
    await same(
      "next lesson link",
      await nextLink.getAttribute("href"),
      `lesson.html?l=${lesson.next}`,
    );
  } else {
    await same("last lesson has no next link", await nextLink.isHidden(), true);
  }
  done.add(id);
}

async function markNextMission(page: Page): Promise<void> {
  await Promise.all([
    page.waitForEvent("load"),
    page.locator("#next .chk").click(),
  ]);
  missionsMarked += 1;
  await see("next card", text(page.locator("#next .k")), /\S/);
}

async function answerReview(page: Page, count: number): Promise<void> {
  for (let k = 0; k < count; k++) {
    const card = page.locator("#repaso .rq").first();
    // Each answer schedules the first review for one day later.
    const numeric = card.locator(".num input");
    if (await numeric.count()) {
      await numeric.fill("0");
      await card.locator(".num button").click();
    } else {
      await card.locator(".opts button").first().click();
    }
    await see(
      "review feedback",
      text(card.locator(".fb .when")),
      "Próximo repaso en 1 día(s).",
    );
    await page.reload();
    reviewsAnswered += 1;
    await see(
      "progress line",
      text(page.locator("#prog")),
      /lecciones completadas/,
    );
    await checkReview(page);
  }
}

async function main(): Promise<void> {
  const { base, stop } = serveSite();
  const browser = await chromium.launch({
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  const context = await newContext(browser, {
    viewport: { width: 1280, height: 900 },
  });
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));

  const [first, second] = lessons;
  const firstLength = lessonOf(first.id).beats.length;
  const secondLength = lessonOf(second.id).beats.length;
  const asksOf = (id: string) => lessonOf(id).beats.filter((b) => b.ask).length;
  const choiceBeats = (id: string) =>
    lessonOf(id).beats.flatMap((b, k) => (b.ask?.kind === "choice" ? [k] : []));
  const [q1, q2] = choiceBeats(first.id);

  try {
    await step("a new learner sees an empty home page", async () => {
      await openHome(page, base);
      await checkHome(page);
    });

    await step("start the first lesson from the home page", async () => {
      await page.locator("#next a.go").click();
      await see(
        "lesson title",
        text(page.locator("#start-title")),
        lessonOf(first.id).title,
      );
      await see(
        "lesson meta",
        text(page.locator("#start-meta")),
        new RegExp(`y ${asksOf(first.id)} preguntas\\.$`),
      );
      await same(
        "no resume offered",
        await page.locator("#resume").isHidden(),
        true,
      );
    });

    await step("begin at 1.5x and go to step 2", async () => {
      await page.locator("#speed").selectOption("1.5");
      await page.locator("#go").click();
      await checkStep(page, 1, firstLength);
      await next(page, 2, firstLength);
    });

    await step("reload mid-lesson and resume at step 2", async () => {
      await page.reload();
      await see(
        "lesson title",
        text(page.locator("#start-title")),
        lessonOf(first.id).title,
      );
      await same(
        "speed kept",
        await page.locator("#speed").inputValue(),
        "1.5",
      );
      await see(
        "resume button",
        text(page.locator("#resume")),
        `Continuar en el paso 2 de ${firstLength}`,
      );
      await page.locator("#resume").click();
      await checkStep(page, 2, firstLength);
    });

    await step("miss then answer the first question", async () => {
      for (let n = 3; n <= q1 + 1; n++) await next(page, n, firstLength);
      await see(
        "step",
        stepLabel(page),
        `Paso ${q1 + 1} de ${firstLength}, con pregunta`,
      );
      await answer(page, first.id, q1, true);
      await page.locator("#ask .next-row .primary").click();
      await checkStep(page, q1 + 2, firstLength);
    });

    await step("answer the second question at the first try", async () => {
      for (let n = q1 + 3; n <= q2 + 1; n++) await next(page, n, firstLength);
      await answer(page, first.id, q2, false);
      await page.locator("#ask .next-row .primary").click();
      await checkStep(page, q2 + 2, firstLength);
    });

    await step("finish the first lesson", async () => {
      await playToEnd(page, q2 + 2, firstLength);
      await finishLesson(page, first.id);
      await see(
        "score",
        text(page.locator("#end-score")),
        "Preguntas acertadas al primer intento: 1 de 2.",
      );
    });

    await step(
      "home shows one lesson done and the pending mission",
      async () => {
        await page.locator("#end a.cta", { hasText: "Índice" }).click();
        await see(
          "progress line",
          text(page.locator("#prog")),
          /lecciones completadas/,
        );
        await checkHome(page);
      },
    );

    await step("answer the review questions of the lesson", async () => {
      await answerReview(page, 1);
      await checkHome(page);
      await answerReview(page, reviewable(first.id) - 1);
      await checkHome(page);
    });

    await step("mark the mission and see the next lesson", async () => {
      await markNextMission(page);
      await checkHome(page);
    });

    await step("mark the first project milestone", async () => {
      await see(
        "milestone",
        text(page.locator("#hito .k")),
        "Hito 1 de 10, parte 1",
      );
      await page.locator("#hito .chk").click();
      await see(
        "milestone",
        text(page.locator("#hito .k")),
        "Hito 2 de 10, parte 2",
      );
      await same(
        "milestones done",
        await page.locator("#track .hito.done").count(),
        1,
      );
      await page.reload();
      await see(
        "milestone after reload",
        text(page.locator("#hito .k")),
        "Hito 2 de 10, parte 2",
      );
      await same(
        "milestones done after reload",
        await page.locator("#track .hito.done").count(),
        1,
      );
      await checkHome(page);
    });

    await step("leave the second lesson half way and come back", async () => {
      await page.locator("#next a.go").click();
      await see(
        "lesson title",
        text(page.locator("#start-title")),
        lessonOf(second.id).title,
      );
      await page.locator("#go").click();
      for (let n = 2; n <= 7; n++) await next(page, n, secondLength);
      await openHome(page, base);
      await checkHome(page);
      await page.locator("#next a.go").click();
      await see(
        "resume button",
        text(page.locator("#resume")),
        `Continuar en el paso 7 de ${secondLength}`,
      );
    });

    await step(
      "go back one step, reload and resume where the learner was",
      async () => {
        await page.locator("#resume").click();
        await checkStep(page, 7, secondLength);
        await page.locator("#prev").click();
        await checkStep(page, 6, secondLength);
        await page.reload();
        await see(
          "resume button",
          text(page.locator("#resume")),
          `Continuar en el paso 6 de ${secondLength}`,
        );
        await page.locator("#resume").click();
        await checkStep(page, 6, secondLength);
      },
    );

    await step("finish the second lesson", async () => {
      await playToEnd(page, 6, secondLength);
      await finishLesson(page, second.id);
    });

    await step("home shows two lessons done and both reviews", async () => {
      await page.locator("#end a.cta", { hasText: "Índice" }).click();
      await see(
        "progress line",
        text(page.locator("#prog")),
        /lecciones completadas/,
      );
      await checkHome(page);
    });

    await step("finish every other lesson in order", async () => {
      await page
        .locator("#parts a", { hasText: lessons[2].title })
        .first()
        .click();
      for (const [k, lesson] of lessons.slice(2).entries()) {
        const total = lessonOf(lesson.id).beats.length;
        await see(
          "lesson title",
          text(page.locator("#start-title")),
          lessonOf(lesson.id).title,
        );
        await page.locator("#go").click();
        await checkStep(page, 1, total);
        await page.locator("#steps").fill(String(total - 1));
        await checkStep(page, total, total);
        await playToEnd(page, total, total);
        await finishLesson(page, lesson.id);
        if (k < lessons.length - 3) await page.locator("#end-next").click();
      }
    });

    await step("home shows the whole course done", async () => {
      await page.locator("#end a.cta", { hasText: "Índice" }).click();
      await see(
        "progress line",
        text(page.locator("#prog")),
        /lecciones completadas/,
      );
      await checkHome(page);
      await same(
        "bar full",
        await page
          .locator("#bar")
          .evaluate((b: HTMLProgressElement) => b.value === b.max),
        true,
      );
    });

    await step(
      "mark the second mission and see the third come up",
      async () => {
        await markNextMission(page);
        await checkHome(page);
      },
    );

    await same("page errors", errors, []);
  } finally {
    await browser.close();
    await stop();
  }
  verify();
}

try {
  await main();
  console.log(`walkthrough passed: ${stepNo} steps`);
} catch (error) {
  console.error(`walkthrough failed: ${(error as Error).message}`);
  process.exit(1);
}
