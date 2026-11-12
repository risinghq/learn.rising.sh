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
interface Block {
  type?: string;
  exercise?: string;
  level?: number;
  starter?: string;
  items?: unknown[];
  body?: unknown[];
}
interface Beat {
  id: string;
  ask?: Ask;
  scene: Block[];
}
interface Lesson {
  title: string;
  next?: string;
  beats: Beat[];
}
interface CourseLesson {
  id: string;
  section: string;
  title: string;
  minutes: number;
}
interface Course {
  parts: { lessons: CourseLesson[] }[];
}
interface Milestone {
  n: number;
  part: number;
  lesson: string;
  exercise: string;
}

const course: Course = JSON.parse(
  readFileSync(join(COURSE_DIR, "course.json"), "utf8"),
);
const { milestones }: { milestones: Milestone[] } = JSON.parse(
  readFileSync(join(COURSE_DIR, "project.json"), "utf8"),
);
const LEVELS = ["", "Reproduce", "Modifica", "Crea"];
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
function exercisesOf(blocks: unknown[]): Block[] {
  return (blocks as Block[]).flatMap((block) =>
    (block.type === "exercise" ? [block] : []).concat(
      exercisesOf((block.items ?? []).concat(block.body ?? [])),
    ),
  );
}

const done = new Set<string>();

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

const METER = ".meter .num";

async function openHome(page: Page, base: string): Promise<void> {
  await page.goto(`${base}/qiskit/`);
  await see("progress line", text(page.locator(METER)), /lecciones$/);
}

// Every row of the map, read from the DOM: the lesson, its state and the unit's count.
const readMap = (page: Page) =>
  page.locator(".unit").evaluateAll((units) =>
    units.map((unit) => ({
      count: unit.querySelector(".count")?.textContent,
      rows: [...unit.querySelectorAll("ol.nodes > li")].map((li) => [
        new URL(
          li.querySelector<HTMLAnchorElement>("a")!.href,
        ).searchParams.get("l"),
        li.querySelector(".node")?.getAttribute("data-state"),
      ]),
    })),
  );

async function checkProgress(page: Page): Promise<void> {
  const total = lessons.length;
  await see(
    "progress line",
    text(page.locator(METER)),
    `${done.size} de ${total} lecciones`,
  );
  await same(
    "progress bar",
    await page
      .locator(".meter progress")
      .evaluate((bar: HTMLProgressElement) => [bar.value, bar.max]),
    [done.size, total],
  );
  // The header shows the streak and the XP only once the learner has progress or an account.
  const stats = page.locator(".stats li");
  if (!done.size) {
    await same(
      "a visitor without progress sees no stats",
      await stats.count(),
      0,
    );
  } else {
    await see(
      "streak",
      async () => (await stats.nth(0).textContent()) ?? "",
      "Racha: 1 día. Empezar un repaso",
    );
    // Every lesson of the walkthrough is finished once, today, for 10 XP.
    await see(
      "xp",
      async () => (await stats.nth(1).textContent()) ?? "",
      `${done.size * 10} XP hoy`,
    );
  }
  const upcoming = lessons.find((l) => !done.has(l.id));
  const expected = course.parts.map((part) => ({
    count: `${part.lessons.filter((l) => done.has(l.id)).length}/${part.lessons.length}`,
    rows: part.lessons.map((l) => [
      l.id,
      done.has(l.id) ? "done" : l === upcoming ? "current" : "locked",
    ]),
  }));
  await same("units and lessons", await readMap(page), expected);
}

async function checkNext(page: Page): Promise<void> {
  const target = lessons.find((l) => !done.has(l.id));
  if (!target) {
    await see(
      "course complete",
      text(page.locator(".complete")),
      "Completaste el curso. Repasa cuando quieras.",
    );
    await same(
      "no current node",
      await page.locator("[data-current]").count(),
      0,
    );
    return;
  }
  const node = page.locator("a[data-current]");
  await see("current node", text(node.locator(".title")), target.title);
  await see(
    "current node button",
    text(node.locator(".go")),
    `${done.size ? "Continuar" : "Empezar"} · ${target.minutes} min`,
  );
  await same(
    "current node link",
    await node.getAttribute("href"),
    `/qiskit/lesson.html?l=${target.id}`,
  );
}

async function checkReview(page: Page): Promise<void> {
  const review = page.locator(".review");
  if (!done.size) {
    await same("review cards before the first lesson", await review.count(), 0);
    return;
  }
  await same(
    "the review card opens the session",
    await review.locator("a.btn").getAttribute("href"),
    "/qiskit/repaso/",
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

async function checkMilestoneExercises(
  page: Page,
  base: string,
  milestone: Milestone,
): Promise<void> {
  const { beats } = lessonOf(milestone.lesson);
  const beat = beats.findIndex((b) =>
    exercisesOf(b.scene).some((x) => x.exercise === milestone.exercise),
  );
  const blocks = exercisesOf(beats[beat].scene);
  await page.goto(
    `${base}/qiskit/lesson.html?l=${milestone.lesson}&beat=${beat}`,
  );
  const panels = page.locator(".xpanel");
  await panels
    .nth(blocks.length - 1)
    .locator(".cm-editor")
    .waitFor();
  await same("exercise panels", await panels.count(), blocks.length);
  for (const [k, block] of blocks.entries()) {
    const panel = panels.nth(k);
    await see(
      `${block.exercise} level`,
      text(panel.locator(".xlevel")),
      LEVELS[block.level!],
    );
    await same(
      `${block.exercise} starter`,
      await panel
        .locator(".cm-line")
        .evaluateAll((lines) => lines.map((l) => l.textContent).join("\n")),
      block.starter,
    );
    await see(
      `${block.exercise} check button`,
      text(panel.locator("button.xbtn.primary")),
      "Comprobar",
    );
  }
}

async function main(): Promise<void> {
  const { base, stop } = serveSite();
  const browser = await chromium.launch({
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  const context = await newContext(browser, {
    viewport: { width: 1280, height: 900 },
    serviceWorkers: "block",
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
    await step("a new learner sees an empty path page", async () => {
      await openHome(page, base);
      await checkHome(page);
    });

    await step("start the first lesson from the path page", async () => {
      await page.locator("a[data-current]").click();
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
      if (q2 === undefined) return;
      for (let n = q1 + 3; n <= q2 + 1; n++) await next(page, n, firstLength);
      await answer(page, first.id, q2, false);
      await page.locator("#ask .next-row .primary").click();
      await checkStep(page, q2 + 2, firstLength);
    });

    await step("finish the first lesson", async () => {
      await playToEnd(page, (q2 ?? q1) + 2, firstLength);
      await finishLesson(page, first.id);
      await see(
        "score",
        text(page.locator("#end-score")),
        `Preguntas acertadas al primer intento: ${q2 === undefined ? 0 : 1} de ${q2 === undefined ? 1 : 2}.`,
      );
    });

    await step("the path shows one lesson done", async () => {
      await page.locator("#end a.cta", { hasText: "Índice" }).click();
      await see("progress line", text(page.locator(METER)), /lecciones$/);
      await checkHome(page);
    });

    await step("open the code exercises of the first milestone", async () => {
      const [milestone] = milestones;
      await see(
        "milestone",
        text(page.locator(".hcur p").first()),
        `Hito 1 de ${milestones.length} · Unidad ${milestone.part}`,
      );
      await page
        .locator(".hcur a.btn", { hasText: "Continuar con el proyecto" })
        .click();
      await see(
        "milestone lesson",
        text(page.locator("#start-title")),
        lessonOf(milestone.lesson).title,
      );
      await checkMilestoneExercises(page, base, milestone);
      await openHome(page, base);
      await checkHome(page);
    });

    await step("mark the first project milestone", async () => {
      await see(
        "milestone",
        text(page.locator(".hcur p").first()),
        "Hito 1 de 10 · Unidad 1",
      );
      await page
        .locator(".hcur .btn", { hasText: "Marcar como hecho" })
        .click();
      await see(
        "milestone",
        text(page.locator(".hcur p").first()),
        "Hito 2 de 10 · Unidad 2",
      );
      await same(
        "milestones done",
        await page.locator(".track .hito[data-state=done]").count(),
        1,
      );
      await page.reload();
      await see(
        "milestone after reload",
        text(page.locator(".hcur p").first()),
        "Hito 2 de 10 · Unidad 2",
      );
      await same(
        "milestones done after reload",
        await page.locator(".track .hito[data-state=done]").count(),
        1,
      );
      await checkHome(page);
    });

    await step("leave the second lesson half way and come back", async () => {
      await page.locator("a[data-current]").click();
      await see(
        "lesson title",
        text(page.locator("#start-title")),
        lessonOf(second.id).title,
      );
      await page.locator("#go").click();
      for (let n = 2; n <= 7; n++) await next(page, n, secondLength);
      await openHome(page, base);
      await checkHome(page);
      await page.locator("a[data-current]").click();
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

    await step(
      "the path shows two lessons done and the review card",
      async () => {
        await page.locator("#end a.cta", { hasText: "Índice" }).click();
        await see("progress line", text(page.locator(METER)), /lecciones$/);
        await checkHome(page);
      },
    );

    await step("finish every other lesson in order", async () => {
      await page.locator("a[data-current]").click();
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

    await step("the path shows the whole course done", async () => {
      await page.locator("#end a.cta", { hasText: "Índice" }).click();
      await see("progress line", text(page.locator(METER)), /lecciones$/);
      await checkHome(page);
      await same(
        "bar full",
        await page
          .locator(".meter progress")
          .evaluate((b: HTMLProgressElement) => b.value === b.max),
        true,
      );
    });

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
