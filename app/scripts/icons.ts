// Renders the committed app icons into site/icons/ with Chromium.
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

import { chromium } from "playwright";

const root = join(import.meta.dirname, "..", "..");

// The sRGB of --a9 and --acc-ink in the light theme. `glyph` is the mark's share of the icon.
const ACCENT = "#654abb";
const INK = "#faf9ff";
// The rising.sh flame, as drawn in risinghq/rising.sh packages/ui/src/Mark.tsx.
const MARK =
  "M12 22A7 7 0 0 1 5 15A8 8 0 0 1 8 8A6 6 0 0 0 10 1A15 15 0 0 1 19 15A7 7 0 0 1 12 22ZM9 16a3 3 0 1 0 6 0a3 3 0 1 0-6 0Z";
const ICONS = [
  { file: "icon-192.png", size: 192, glyph: 0.62, radius: 0.22 },
  { file: "icon-512.png", size: 512, glyph: 0.62, radius: 0.22 },
  { file: "apple-touch-icon.png", size: 180, glyph: 0.62, radius: 0 },
  // A maskable icon is cropped by the system to a shape, so its mark stays in the middle 60%.
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
    html { background: transparent; }
    body { margin: 0; width: ${size}px; height: ${size}px; display: grid; place-items: center;
      background: ${ACCENT}; border-radius: ${radius * size}px; }
  </style><body><svg width="${glyph * size}" height="${glyph * size}" viewBox="0 0 24 24">
    <path d="${MARK}" fill="${INK}" fill-rule="evenodd"/></svg></body>`);
    await page.screenshot({ path: join(out, file), omitBackground: true });
  }),
);
await browser.close();
