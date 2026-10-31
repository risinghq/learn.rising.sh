import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: [
      "tests/**/*.test.ts",
      "drill/**/*.test.ts",
      "app/src/**/*.test.ts",
    ],
    testTimeout: 60_000,
  },
});
