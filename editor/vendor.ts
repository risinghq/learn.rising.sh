// Copy KaTeX into the output directory so the site serves it itself.
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

if (!process.argv[2]) throw new Error("usage: node vendor.ts OUTPUT_DIR");
const out = resolve(process.argv[2]);
const modules = join(dirname(fileURLToPath(import.meta.url)), "node_modules");

await rm(out, { recursive: true, force: true });
await mkdir(join(out, "katex", "fonts"), { recursive: true });

// Browsers use woff2 here, so drop the woff and ttf fallbacks from KaTeX's CSS.
const dist = join(modules, "katex", "dist");
const katexCss = (await readFile(join(dist, "katex.min.css"), "utf8")).replace(
  /,url\(fonts\/[^)]+\.woff\) format\("woff"\),url\(fonts\/[^)]+\.ttf\) format\("truetype"\)/g,
  "",
);
await writeFile(join(out, "katex", "katex.min.css"), katexCss);
const copies = [
  cp(join(dist, "katex.min.js"), join(out, "katex", "katex.min.js")),
];
for (const [, file] of katexCss.matchAll(/url\(fonts\/([^)]+)\)/g))
  copies.push(cp(join(dist, "fonts", file), join(out, "katex", "fonts", file)));
await Promise.all(copies);
