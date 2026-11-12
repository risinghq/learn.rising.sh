// Builds the shell into site/: hashed assets, prerendered pages and a service worker.
// Every route comes from site/courses.json, so adding a course requires no route code.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { build } from "vite";

import type { Course, CoursePage, Page, Part, Project } from "../src/model.ts";
import { headTags } from "./head-tags.ts";

const app = fileURLToPath(new URL("..", import.meta.url));
const site = join(app, "..", "site");
const dist = join(app, "dist");

const json = async <T>(file: string): Promise<T> =>
  JSON.parse(await readFile(file, "utf8")) as T;
const exists = (file: string) =>
  readFile(file).then(
    () => true,
    () => false,
  );

async function readPages(): Promise<
  { route: string; file: string; page: Page }[]
> {
  const courses = await json<Course[]>(join(site, "courses.json"));
  const pages = await Promise.all(
    courses.map(async (course): Promise<CoursePage> => {
      if (!course.title || !course.outcome)
        throw new Error(
          `courses.json: ${course.slug} needs a title and an outcome`,
        );
      if (!(await exists(join(site, course.slug, "items.json"))))
        throw new Error(
          `${course.slug}/items.json is missing: run mise run generate:items`,
        );
      const projectFile = join(site, course.slug, "project.json");
      const [{ parts, guides = [] }, project] = await Promise.all([
        json<{ parts: Part[]; guides?: Part["lessons"] }>(
          join(site, course.slug, "course.json"),
        ),
        exists(projectFile).then((found) =>
          found ? json<Project>(projectFile) : undefined,
        ),
      ]);
      for (const m of project?.milestones ?? [])
        if (!parts[m.part - 1])
          throw new Error(
            `${course.slug}/project.json: milestone ${m.n} names part ${m.part}`,
          );
      return { kind: "course", course, parts, guides, project };
    }),
  );
  return [
    {
      route: "/",
      file: "index.html",
      page: {
        kind: "catalog",
        courses: pages.map(({ course, parts }) => ({
          course,
          lessons: parts
            .flatMap((p) => p.lessons)
            .map(({ id, section, title, minutes }) => ({
              id,
              section,
              title,
              minutes,
            })),
        })),
      },
    },
    { route: "/amigos/", file: "amigos/index.html", page: { kind: "friends" } },
    {
      route: "/privacidad.html",
      file: "privacidad.html",
      page: { kind: "privacy" },
    },
    ...pages.flatMap((page) => [
      {
        route: `/${page.course.slug}/`,
        file: `${page.course.slug}/index.html`,
        page,
      },
      {
        route: `/${page.course.slug}/repaso/`,
        file: `${page.course.slug}/repaso/index.html`,
        page: { kind: "session" as const, course: page.course },
      },
    ]),
  ];
}

await rm(dist, { recursive: true, force: true });
await build({ root: app, logLevel: "warn", build: { outDir: dist } });
await build({
  root: app,
  logLevel: "warn",
  build: {
    ssr: "src/entry-server.tsx",
    outDir: join(dist, "server"),
    emptyOutDir: true,
  },
});

const template = await readFile(join(dist, "index.html"), "utf8");
const outlet = '<div id="root"><!--ssr-outlet--></div>';
const slot = "<!--page-metadata-->";
if (!template.includes(outlet) || !template.includes(slot))
  throw new Error("dist/index.html is not the template");

const { render } = (await import(
  pathToFileURL(join(dist, "server", "entry-server.js")).href
)) as {
  render: (page: Page) => string;
};
const assets = await readdir(join(dist, "assets"));
// theme.css declares the face; the shell only preloads its main range.
const mainFont = "/fonts/inter-latin-wght-normal.woff2";

const revision =
  process.env.GITHUB_SHA ??
  (() => {
    try {
      return execFileSync("git", ["rev-parse", "HEAD"], {
        encoding: "utf8",
      }).trim();
    } catch {
      return undefined;
    }
  })();

const pages = await readPages();
const precache = new Set<string>([
  "/theme.css",
  "/theme.js",
  "/account.js",
  "/courses.json",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  mainFont,
  "/fonts/inter-latin-ext-wght-normal.woff2",
  ...assets.map((f) => `/assets/${f}`),
]);
const hash = createHash("sha256");

await rm(join(site, "assets"), { recursive: true, force: true });
await cp(join(dist, "assets"), join(site, "assets"), { recursive: true });

const rendered = pages.map(({ route, file, page }) => {
  // `<` in the data would end the script element early.
  const data = JSON.stringify(page).replaceAll("<", "\\u003c");
  const html = template
    .replace(slot, headTags(page, mainFont, revision))
    .replace(
      outlet,
      `<div id="root">${render(page)}</div>\n    <script id="page-data" type="application/json">${data}</script>`,
    );
  hash.update(html);
  precache.add(route);
  if (page.kind === "course") {
    precache.add(`/${page.course.slug}/course.json`);
    precache.add(`/${page.course.slug}/items.json`);
  }
  return { file: join(site, file), html };
});
await Promise.all(
  rendered.map(async ({ file, html }) => {
    await mkdir(dirname(file), { recursive: true });
    await writeFile(file, html);
  }),
);

const pyodide = JSON.parse(
  await readFile(
    join(app, "..", "editor", "node_modules", "pyodide", "package.json"),
    "utf8",
  ),
) as { version: string };
const worker = (await readFile(join(app, "scripts", "sw.js"), "utf8"))
  .replace("__VERSION__", hash.digest("hex").slice(0, 12))
  .replace("__PYODIDE__", pyodide.version)
  .replace('"__PRECACHE__"', JSON.stringify([...precache].toSorted()));
await writeFile(join(site, "sw.js"), worker);

await rm(dist, { recursive: true, force: true });
console.log(`shell: ${pages.length} pages, ${precache.size} precached files`);
