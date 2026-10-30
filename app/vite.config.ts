import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const path = (relative: string) =>
  fileURLToPath(new URL(relative, import.meta.url));

// The build stages its output in dist/; scripts/build.ts prerenders the pages
// from it and writes the result into site/.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@site": path("../site"),
      "@fonts": path("node_modules/@fontsource-variable/inter/files"),
    },
  },
  build: {
    target: "es2023",
    cssCodeSplit: false,
    assetsInlineLimit: 0,
  },
});
