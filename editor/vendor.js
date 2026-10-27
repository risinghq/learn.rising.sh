// Copy KaTeX and the fonts into the output directory so the site serves them
// itself.
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

if (!process.argv[2]) throw new Error("usage: node vendor.js OUTPUT_DIR");
const out = resolve(process.argv[2]);
const modules = join(dirname(fileURLToPath(import.meta.url)), "node_modules");

// The site needs only these Unicode ranges.
const SUBSETS = new Set(["latin", "latin-ext"]);

// Keep the family names used by the site's CSS. Variable fonts replace the
// static weights requested by the pages.
const FONTS = [
  { family: "Newsreader", pkg: "newsreader", css: "opsz.css" },
  { family: "JetBrains Mono", pkg: "jetbrains-mono", css: "wght.css" },
];

await rm(out, { recursive: true, force: true });
await mkdir(join(out, "fonts"), { recursive: true });
await mkdir(join(out, "katex", "fonts"), { recursive: true });

const copies = [];

const faces = (
  await Promise.all(
    FONTS.map(async ({ family, pkg, css }) => {
      const dir = join(modules, "@fontsource-variable", pkg);
      const source = await readFile(join(dir, css), "utf8");
      const wanted = [];
      for (const block of source.split(/\n\n+/)) {
        const subset = /^\/\* \S+?-(latin(?:-ext)?)-\w+-normal \*\//.exec(
          block.trim(),
        );
        if (!subset || !SUBSETS.has(subset[1])) continue;
        const file = /url\(\.\/files\/([^)]+)\)/.exec(block)[1];
        copies.push(cp(join(dir, "files", file), join(out, "fonts", file)));
        wanted.push(
          block
            .replace(/^\/\*.*\*\/\n/, "")
            .replace(`'${family} Variable'`, `"${family}"`)
            .replace("./files/", "fonts/")
            .replace("format('woff2-variations')", 'format("woff2")'),
        );
      }
      return wanted;
    }),
  )
).flat();
await writeFile(join(out, "fonts.css"), `${faces.join("\n\n")}\n`);

// Browsers use woff2 here, so drop the woff and ttf fallbacks from KaTeX's CSS.
const dist = join(modules, "katex", "dist");
const katexCss = (await readFile(join(dist, "katex.min.css"), "utf8")).replace(
  /,url\(fonts\/[^)]+\.woff\) format\("woff"\),url\(fonts\/[^)]+\.ttf\) format\("truetype"\)/g,
  "",
);
await writeFile(join(out, "katex", "katex.min.css"), katexCss);
copies.push(cp(join(dist, "katex.min.js"), join(out, "katex", "katex.min.js")));
for (const [, file] of katexCss.matchAll(/url\(fonts\/([^)]+)\)/g))
  copies.push(cp(join(dist, "fonts", file), join(out, "katex", "fonts", file)));
await Promise.all(copies);
