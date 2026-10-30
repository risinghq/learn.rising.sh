// The script budget of the shell, on the built site/:
//     bun tests/budget_test.ts
// A page may load at most 100 KB of gzipped JavaScript. The player and editor bundles belong to the
// lesson page and do not count, because no shell page loads them.
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { gzipSync } from "node:zlib";

const SITE = resolve(import.meta.dirname, "..", "site");
const BUDGET = 100 * 1024;
const courses = JSON.parse(
  readFileSync(join(SITE, "courses.json"), "utf8"),
) as { slug: string }[];
const PAGES = ["/", "/privacidad.html", ...courses.map((c) => `/${c.slug}/`)];

const failures: string[] = [];
for (const route of PAGES) {
  const html = readFileSync(
    join(SITE, route.endsWith("/") ? `${route}index.html` : route),
    "utf8",
  );
  const sources = [
    ...html.matchAll(/<script\b[^>]*\bsrc="([^"]+)"/g),
    ...html.matchAll(/<link\b[^>]*rel="modulepreload"[^>]*\bhref="([^"]+)"/g),
  ].map((m) => m[1]);
  const sizes = sources.map((src) => ({
    src,
    bytes: gzipSync(readFileSync(join(SITE, src))).length,
  }));
  const total = sizes.reduce((sum, s) => sum + s.bytes, 0);
  const detail = sizes
    .map((s) => `${s.src} ${(s.bytes / 1024).toFixed(1)} KB`)
    .join(", ");
  console.log(`${route}: ${(total / 1024).toFixed(1)} KB gzip (${detail})`);
  if (sizes.length === 0) failures.push(`${route} loads no script`);
  if (total > BUDGET)
    failures.push(
      `${route} loads ${(total / 1024).toFixed(1)} KB of gzipped JavaScript, over the ${BUDGET / 1024} KB budget`,
    );
}
for (const failure of failures) console.error(`FAIL ${failure}`);
process.exit(failures.length ? 1 : 0);
