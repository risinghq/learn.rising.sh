// Friends, the weekly board and the streak reminder at 390x844, with two accounts
// on the local Worker: A invites and shares the link, B signs in and accepts,
// both see each other on the board, and B removes A. It also covers the header,
// the lesson and exercise XP sources, the offline queue, the first sign-in seed
// and the reminder opt-in.
//     bun tests/friends_test.ts
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { isDeepStrictEqual } from "node:util";

import { chromium } from "playwright";
import type { BrowserContextOptions, Page } from "playwright";

import { verify } from "./offline.ts";
import {
  call,
  newTab,
  routeProvider,
  startWorker,
  stopWorker,
  type Tab,
} from "./worker.ts";

const ROOT = resolve(import.meta.dirname, "..");
const PHONE: BrowserContextOptions = {
  viewport: { width: 390, height: 844 },
  permissions: ["clipboard-read", "clipboard-write"],
};
const LESSON = "p1-quickstart";
const EXERCISE = "p1-quickstart/ghz";
const PASSING = "print('hola')\n";

const failures: string[] = [];
function check(ok: boolean, message: string): void {
  if (!ok) failures.push(message);
  console.log(ok ? "✓" : "✗", message);
}

type Rows = Record<string, number>;
interface Post {
  source: string;
  ref: string;
  amount: number;
  tz?: string;
  earnedAt?: number;
}

// The browser has no push service offline, so a subscription is made here: a
// real P-256 key and an endpoint on the host the Worker allows.
const fakePush = (host: string) => `
(() => {
  // The page keeps its subscription across a reload, as a browser does.
  const KEY = "fake:push";
  const saved = JSON.parse(localStorage.getItem(KEY) ?? "null");
  let permission = saved ? "granted" : "default";
  let subscription = null;
  const remember = () =>
    localStorage.setItem(KEY, JSON.stringify(subscription && subscription.toJSON()));
  const make = (endpoint, keys) => ({
    endpoint,
    toJSON: () => ({ endpoint, keys }),
    unsubscribe: async () => { subscription = null; localStorage.removeItem(KEY); return true; },
  });
  if (saved) subscription = make(saved.endpoint, saved.keys);
  Object.defineProperty(Notification, "permission", { get: () => permission });
  Notification.requestPermission = async () => (permission = "granted");
  const b64 = (bytes) =>
    btoa(String.fromCharCode(...new Uint8Array(bytes)))
      .replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
  PushManager.prototype.getSubscription = async () => subscription;
  PushManager.prototype.subscribe = async () => {
    const pair = await crypto.subtle.generateKey(
      { name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
    const raw = await crypto.subtle.exportKey("raw", pair.publicKey);
    const keys = {
      p256dh: b64(raw),
      auth: b64(crypto.getRandomValues(new Uint8Array(16))),
    };
    const endpoint = "https://${host}/push/" + b64(crypto.getRandomValues(new Uint8Array(8)));
    subscription = make(endpoint, keys);
    remember();
    return subscription;
  };
})();`;

const FAKE_SHARE = `
window.shared = [];
navigator.share = async (data) => { window.shared.push(data); };`;

function recordXp(page: Page): Post[] {
  const sent: Post[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().endsWith("/api/xp")) {
      sent.push(request.postDataJSON() as Post);
    }
  });
  return sent;
}

const pad = (n: number) => String(n).padStart(2, "0");
function localDay(): string {
  const now = new Date();
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

const earn = (page: Page, ref: string, amount: number) =>
  page.evaluate(
    ([id, n]) =>
      (
        window as unknown as {
          QGAccount: {
            xp: (source: string, ref: string, amount: number) => void;
          };
        }
      ).QGAccount.xp("drill", id as string, n as number),
    [ref, amount] as const,
  );

// The refs queued under an owner: an account id, or "anon".
const queued = (page: Page, owner: string) =>
  page.evaluate(
    (who) =>
      (
        JSON.parse(localStorage.getItem(`rising:xpq:${who}`) ?? "[]") as {
          ref: string;
        }[]
      ).map((post) => post.ref),
    owner,
  );

// The player is a deferred script that fetches the lesson before it binds #go, and it fills
// #start-meta in the same task as the binding. A click before that does nothing, and the start
// overlay then blocks every later click.
async function begin(page: Page) {
  await page.locator("#start-meta").filter({ hasText: "preguntas" }).waitFor();
  await page.locator("#go").click();
}

// Waits until the signed-in account has nothing left to send.
const emptied = (page: Page) =>
  page.waitForFunction(
    () =>
      localStorage.getItem(
        `rising:xpq:${localStorage.getItem("rising:cuenta")}`,
      ) === null,
  );

const header = (page: Page) => page.locator("header.top .stats");

async function signIn(page: Page): Promise<void> {
  await page.getByRole("link", { name: "Entrar con GitHub" }).click();
  await page.getByRole("heading", { name: "Tu racha" }).waitFor();
}

function missionUrl(lesson: string): string {
  const { beats } = JSON.parse(
    readFileSync(
      join(ROOT, "site", "qiskit", "lessons", lesson, "lesson.json"),
      "utf8",
    ),
  ) as { beats: { id: string }[] };
  return `/qiskit/lesson.html?l=${lesson}&beat=${beats.findIndex((beat) => beat.id === "mision")}`;
}

function lastBeat(lesson: string): number {
  const { beats } = JSON.parse(
    readFileSync(
      join(ROOT, "site", "qiskit", "lessons", lesson, "lesson.json"),
      "utf8",
    ),
  ) as { beats: unknown[] };
  return beats.length - 1;
}

async function account(
  tab: Tab,
  site: string,
): Promise<{ total: number; today: number }> {
  return (await (await tab.context.request.get(`${site}/api/xp`)).json()) as {
    total: number;
    today: number;
  };
}

const rowsOf = (page: Page, selector: string) =>
  page.locator(selector).allInnerTexts();

async function main(): Promise<void> {
  const { process: worker, urls } = await startWorker();
  const { site, control } = urls;
  try {
    const browser = await chromium.launch();

    const a = await newTab(browser, site, control, "7001", PHONE);
    await a.context.addInitScript(FAKE_SHARE);
    await a.context.addInitScript(fakePush(urls.pushHost));
    const sentA = recordXp(a.page);

    // Without an account the page asks for a sign-in and never calls the account.
    await a.page.goto(`${site}/amigos/`);
    await a.page.getByRole("link", { name: "Entrar con GitHub" }).waitFor();
    check(
      (await a.page.locator("table").count()) === 0,
      "signed out: no board",
    );
    check(
      !a.requests.some(([, path]) => path.startsWith("/api/")),
      "signed out: the page makes no account request",
    );

    // XP earned before the first sign-in is posted once at sign-in.
    const day = localDay();
    await a.page.evaluate(
      ([key, today]) =>
        localStorage.setItem(key, JSON.stringify({ [today]: 7 })),
      ["rising:xp", day] as const,
    );
    await signIn(a.page);
    await a.page.waitForFunction(() =>
      /7\s*XP/.test(document.querySelector("header .stats")?.textContent ?? ""),
    );
    check(
      (await account(a, site)).total === 7,
      "first sign-in: the XP earned before it is in the account",
    );
    check(
      sentA.length === 1 && sentA[0].source === "drill",
      `first sign-in: it is posted once (${JSON.stringify(sentA)})`,
    );
    await a.page.reload();
    await a.page.getByRole("heading", { name: "Tu racha" }).waitFor();
    await a.page.waitForTimeout(500);
    check(sentA.length === 1, "reload: the earlier XP is not posted again");

    // The header reads the account.
    check(
      /Racha:\s*1\s*día/.test(await header(a.page).innerText()) &&
        /7\s*XP/.test(await header(a.page).innerText()),
      `header: the streak and today's XP come from the account (${JSON.stringify(await header(a.page).innerText())})`,
    );

    // No friends: the board shows the invite action and no table.
    check(
      (await a.page.locator("table").count()) === 0,
      "no friends: no empty table",
    );
    await a.page.getByRole("button", { name: "Invitar a un amigo" }).waitFor();

    // A invites and shares the link.
    await a.page.getByRole("button", { name: "Invitar a un amigo" }).click();
    await a.page.getByRole("button", { name: "Compartir enlace" }).click();
    await a.page.getByText("Invitación compartida.").waitFor();
    const shared = await a.page.evaluate(
      () => (window as unknown as { shared: { url: string }[] }).shared,
    );
    const link = shared[0]?.url ?? "";
    check(
      shared.length === 1 && link.startsWith(`${site}/amigos/?c=`),
      `invite: the share sheet gets the link (${link})`,
    );
    check(
      (await a.page.getByLabel("Enlace de invitación").inputValue()) === link,
      "invite: the link is also shown to copy",
    );

    // B opens the link, signs in and comes back to it.
    const b = await newTab(browser, site, control, "7002", PHONE);
    await b.context.addInitScript(fakePush(urls.pushHost));
    await b.page.goto(link);
    await b.page
      .getByRole("heading", {
        name: "Te invitaron a Rising. Entra para aceptar",
      })
      .waitFor();
    await b.page.getByRole("link", { name: "Entrar con GitHub" }).click();
    await b.page.getByRole("button", { name: "Aceptar invitación" }).waitFor();
    check(
      new URL(b.page.url()).searchParams.get("c") !== null,
      "accept: signing in returns to the invitation",
    );
    await earn(b.page, "b:1", 12);
    await b.page.getByRole("button", { name: "Aceptar invitación" }).click();
    await b.page.getByText("Ahora son amigos.").waitFor();
    check(
      new URL(b.page.url()).search === "",
      "accept: the code leaves the address",
    );

    // Both see each other on the board, B ahead with 12 against 7.
    await b.page.getByRole("table").waitFor();
    check(
      isDeepStrictEqual(
        (await rowsOf(b.page, ".board tbody tr")).map((row) =>
          row.replaceAll(/\s+/g, " "),
        ),
        ["1 Tú 12", "2 Amigo 1 7"],
      ),
      `B: the board ranks B first with A second (${JSON.stringify(await rowsOf(b.page, ".board tbody tr"))})`,
    );
    check(
      /1\s+día/.test(await b.page.locator(".friends li").first().innerText()),
      `B: the friend list shows A's streak (${JSON.stringify(await b.page.locator(".friends li").first().innerText())})`,
    );
    check(
      /domingo|lunes|martes|miércoles|jueves|viernes|sábado/.test(
        await b.page.getByText(/Termina el/).innerText(),
      ),
      "B: the board shows when the week ends",
    );

    await a.page.reload();
    await a.page.getByRole("table").waitFor();
    check(
      isDeepStrictEqual(
        (await rowsOf(a.page, ".board tbody tr")).map((row) =>
          row.replaceAll(/\s+/g, " "),
        ),
        ["1 Amigo 1 12", "2 Tú 7"],
      ),
      `A: the board ranks B first with A second (${JSON.stringify(await rowsOf(a.page, ".board tbody tr"))})`,
    );
    check(
      (await a.page.locator(".friends li").count()) === 1,
      "A: the friend list holds B",
    );
    check(
      (await a.page.locator('.board tr[data-you="true"]').count()) === 1,
      "A: the learner's own row is marked",
    );

    for (const [name, page] of [
      ["A", a.page],
      ["B", b.page],
    ] as const) {
      check(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        `${name}: the friends page does not scroll sideways at 390 px`,
      );
    }

    // B removes A after a confirmation.
    await b.page.getByRole("button", { name: "Quitar a Amigo 1" }).click();
    await b.page.getByRole("button", { name: "Conservar" }).click();
    check(
      (await b.page.locator(".friends li").count()) === 1,
      "B: keeping the friend leaves the list as it was",
    );
    await b.page.getByRole("button", { name: "Quitar a Amigo 1" }).click();
    await b.page.getByRole("button", { name: "Quitar amigo" }).click();
    await b.page.locator("table").waitFor({ state: "detached" });
    await b.page.getByRole("button", { name: "Invitar a un amigo" }).waitFor();
    check(
      (await b.page.locator("table").count()) === 0,
      "B: with no friend left the board gives way to the invite action",
    );
    await a.page.reload();
    await a.page.getByRole("button", { name: "Invitar a un amigo" }).waitFor();
    check(
      (await a.page.locator("table").count()) === 0,
      "A: B's removal reaches A",
    );
    check(
      (await call<Rows>(`${control}/rows`)).friendships === 0,
      "removal: no friendship is left in the account",
    );

    // Where the browser has no share sheet the link is copied.
    await b.page.getByRole("button", { name: "Invitar a un amigo" }).click();
    check(
      (await b.page
        .getByRole("button", { name: "Compartir enlace" })
        .count()) === 0,
      "copy: a browser without Web Share offers no share button",
    );
    await b.page.getByRole("button", { name: "Copiar enlace" }).click();
    await b.page.getByText("Enlace copiado.").waitFor();
    check(
      (await b.page.evaluate(() => navigator.clipboard.readText())) ===
        (await b.page.getByLabel("Enlace de invitación").inputValue()),
      "copy: the clipboard holds the invitation link",
    );

    // The streak reminder: opt in, and the account holds the browser.
    await b.page
      .getByRole("button", { name: "Avisarme si olvido mi racha" })
      .click();
    await b.page.getByText(/Te avisamos a las 19:00/).waitFor();
    check(
      (await call<Rows>(`${control}/rows`)).push_subscriptions === 1,
      "reminder: the account stores the browser",
    );
    await b.page.reload();
    await b.page
      .getByRole("button", { name: "Quitar el aviso de racha" })
      .waitFor();
    await b.page
      .getByRole("button", { name: "Quitar el aviso de racha" })
      .click();
    await b.page
      .getByRole("button", { name: "Avisarme si olvido mi racha" })
      .waitFor();
    check(
      (await call<Rows>(`${control}/rows`)).push_subscriptions === 0,
      "reminder: turning it off drops the browser",
    );

    // XP earned offline waits in the queue and is sent when the connection returns.
    const before = (await account(a, site)).total;
    await a.context.setOffline(true);
    await earn(a.page, "off:1", 5);
    await a.page.waitForFunction(
      () =>
        (
          JSON.parse(
            localStorage.getItem(
              `rising:xpq:${localStorage.getItem("rising:cuenta")}`,
            ) ?? "[]",
          ) as unknown[]
        ).length === 1,
    );
    check(
      /12\s*XP/.test(await header(a.page).innerText()),
      `offline: the header counts the XP that waits (${await header(a.page).innerText()})`,
    );
    await a.context.setOffline(false);
    await emptied(a.page);
    check(
      (await account(a, site)).total === before + 5,
      "offline: the queued XP reaches the account once",
    );

    // A lesson and an exercise post their own source.
    await a.page.goto(
      `${site}/qiskit/lesson.html?l=${LESSON}&beat=${lastBeat(LESSON)}`,
    );
    await a.page.locator("#next").click();
    await a.page.locator("#end:not(.hide)").waitFor();
    await a.page.goto(`${site}${missionUrl(LESSON)}`);
    const panel = a.page.locator(".xpanel").nth(1);
    await panel.locator(".cm-editor").waitFor();
    await panel.locator(".cm-content").click();
    await a.page.keyboard.press("ControlOrMeta+A");
    await a.page.keyboard.insertText(PASSING);
    await panel.getByRole("button", { name: "Comprobar" }).click();
    await panel.locator(".xstatus.ok").waitFor({ timeout: 40_000 });
    await emptied(a.page);
    const sources = sentA.map((post) => `${post.source}:${post.ref}`);
    check(
      sources.includes(`lesson:${LESSON}`),
      `lesson: completing it posts source lesson (${JSON.stringify(sources)})`,
    );
    check(
      sources.includes(`exercise:${EXERCISE}`),
      `exercise: passing it posts source exercise (${JSON.stringify(sources)})`,
    );

    // A queued post counts in the header only when it was earned today.
    await a.page.goto(`${site}/`);
    await a.page.route("**/api/xp", (route) => route.abort());
    const shown = await header(a.page).innerText();
    await a.page.evaluate(() => {
      const key = `rising:xpq:${localStorage.getItem("rising:cuenta")}`;
      localStorage.setItem(
        key,
        JSON.stringify([
          {
            source: "drill",
            ref: "old:1",
            amount: 40,
            earnedAt: Date.now() - 30 * 3600_000,
          },
        ]),
      );
    });
    await a.page.reload();
    check(
      (await header(a.page).innerText()) === shown,
      `queue: an earlier day's post is not today's XP (${shown} -> ${await header(a.page).innerText()})`,
    );
    await a.page.evaluate(() =>
      localStorage.removeItem(
        `rising:xpq:${localStorage.getItem("rising:cuenta")}`,
      ),
    );

    // Each account has its own queue. A's unsent XP stays under A's key through sign-out; B signs in
    // on the same browser and sends only B's own and the XP earned before any account.
    await a.page.goto(`${site}/qiskit/lesson.html?l=${LESSON}`);
    await begin(a.page);
    await earn(a.page, "left:1", 3);
    const idA = await a.page.evaluate(() =>
      localStorage.getItem("rising:cuenta"),
    );
    const totalA = (await account(a, site)).total;
    check(
      isDeepStrictEqual(await queued(a.page, idA!), ["left:1"]),
      `sign-out: the unsent post waits in A's queue (${JSON.stringify(await queued(a.page, idA!))})`,
    );
    await a.page.getByRole("button", { name: "Cuenta ✓", exact: true }).click();
    await a.page
      .getByRole("button", { name: "Cerrar sesión", exact: true })
      .click();
    await a.page.getByRole("button", { name: "Entrar", exact: true }).waitFor();
    check(
      isDeepStrictEqual(await queued(a.page, idA!), ["left:1"]),
      "sign-out: A's queue is left alone",
    );
    await a.page.unroute("**/api/xp");
    await a.page.evaluate(() =>
      localStorage.setItem(
        "rising:xpq:anon",
        JSON.stringify([
          { source: "drill", ref: "anon:1", amount: 4, earnedAt: Date.now() },
        ]),
      ),
    );
    const beforeB = sentA.length;
    await routeProvider(a.context, control, "7003");
    await a.page
      .getByRole("button", { name: "Entrar con GitHub", exact: true })
      .click();
    await a.page
      .getByRole("button", { name: "Cuenta ✓", exact: true })
      .waitFor();
    await emptied(a.page);
    await a.page.waitForTimeout(500);
    const sentToB = sentA.slice(beforeB).map((post) => post.ref);
    check(
      !sentToB.includes("left:1"),
      `sign-in as B: no request carries A's post (${JSON.stringify(sentToB)})`,
    );
    check(
      sentToB.includes("anon:1") && (await account(a, site)).total === 4,
      `sign-in as B: the post from before any account is sent (${JSON.stringify(sentToB)})`,
    );
    check(
      (await a.page.evaluate(() => localStorage.getItem("rising:xpq:anon"))) ===
        null,
      "sign-in as B: the anonymous queue is gone",
    );

    // A signs back in later and A's post is still sent.
    await begin(a.page);
    await a.page.getByRole("button", { name: "Cuenta ✓", exact: true }).click();
    await a.page
      .getByRole("button", { name: "Cerrar sesión", exact: true })
      .click();
    await a.page.getByRole("button", { name: "Entrar", exact: true }).waitFor();
    await routeProvider(a.context, control, "7001");
    await a.page
      .getByRole("button", { name: "Entrar con GitHub", exact: true })
      .click();
    await a.page
      .getByRole("button", { name: "Cuenta ✓", exact: true })
      .waitFor();
    await emptied(a.page);
    check(
      sentA.slice(beforeB).some((post) => post.ref === "left:1") &&
        (await account(a, site)).total === totalA + 3,
      `sign-in as A again: A's post is sent (${(await account(a, site)).total} of ${totalA + 3})`,
    );

    // A queue left by an earlier version belongs to no one on a device where nobody signed in:
    // it joins the first sign-in. Without a date it is never today's XP.
    const c = await newTab(browser, site, control, "7004", PHONE);
    const sentC = recordXp(c.page);
    await c.page.goto(`${site}/amigos/`);
    await c.page.evaluate(() =>
      localStorage.setItem(
        "rising:xpq",
        JSON.stringify([{ ref: "legacy:1", amount: 40 }]),
      ),
    );
    await c.page.reload();
    await c.page.getByRole("link", { name: "Entrar con GitHub" }).waitFor();
    await c.page.route("**/api/xp", (route) => route.abort());
    await signIn(c.page);
    await c.page.waitForFunction(
      () =>
        localStorage.getItem("rising:xpq") === null &&
        localStorage.getItem("rising:xpq:anon") === null,
    );
    const legacyHeader = await header(c.page).innerText();
    check(
      /\b0\s*XP/.test(legacyHeader) &&
        sentC.some((post) => post.ref === "legacy:1" && post.earnedAt === 0),
      `legacy: an undated post is not today's XP (${JSON.stringify(legacyHeader)})`,
    );
    await c.page.unroute("**/api/xp");
    await c.page.evaluate(() => dispatchEvent(new Event("online")));
    await emptied(c.page);
    check(
      (await account(c, site)).total === 40,
      "legacy: the undated post is still sent",
    );

    for (const tab of [a, b, c]) {
      check(
        isDeepStrictEqual(tab.errors, []),
        `no page errors ${JSON.stringify(tab.errors)}`,
      );
    }
    await browser.close();
  } finally {
    await stopWorker(worker);
  }
  verify();
  console.log(failures.length ? `\n${failures.length} failures` : "\nall good");
  process.exit(failures.length ? 1 : 0);
}

await main();
