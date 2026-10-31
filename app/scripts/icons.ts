// Renders the committed app icons into site/icons/ with Chromium.
import { mkdir, readFile } from "node:fs/promises";
import { join } from "node:path";

import { chromium } from "playwright";

const root = join(import.meta.dirname, "..", "..");
const font = await readFile(
  join(root, "site", "fonts", "inter-latin-wght-normal.woff2"),
);

// The sRGB of --a9 and --acc-ink in the light theme. `glyph` is the letter's share of the icon.
const ACCENT = "#654abb";
const INK = "#faf9ff";
const ICONS = [
  { file: "icon-192.png", size: 192, glyph: 0.62, radius: 0.22 },
  { file: "icon-512.png", size: 512, glyph: 0.62, radius: 0.22 },
  { file: "apple-touch-icon.png", size: 180, glyph: 0.62, radius: 0 },
  // A maskable icon is cropped by the system to a shape, so its letter stays in the middle 60%.
  { file: "icon-maskable-512.png", size: 512, glyph: 0.46, radius: 0 },
];

const out = join(root, "site", "icons");
await mkdir(out, { recursive: true });
const browser = await chromium.launch();
await Promise.all(
  ICONS.map(async ({ file, size, glyph, radius }) => {
    const page = await browser.newPage({
      viewport: { width: size, height: size },
    });
    await page.setContent(`<style>
    @font-face { font-family: Inter; font-weight: 100 900; src: url(data:font/woff2;base64,${font.toString("base64")}); }
    html { background: transparent; }
    body { margin: 0; width: ${size}px; height: ${size}px; display: grid; place-items: center;
      background: ${ACCENT}; color: ${INK}; border-radius: ${radius * size}px;
      font: 600 ${glyph * size}px/1 Inter; letter-spacing: -0.04em; }
  </style><body>R</body>`);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: join(out, file), omitBackground: true });
  }),
);
await browser.close();
