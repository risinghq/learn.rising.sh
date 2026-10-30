import { writeFileSync } from "node:fs";
import { join } from "node:path";

import { ItemError, SITE, buildBank, courses } from "./bank.ts";

try {
  for (const course of courses()) {
    const bank = buildBank(course);
    writeFileSync(join(SITE, course, "items.json"), JSON.stringify(bank));
    console.log(`site/${course}/items.json: ${bank.items.length} items`);
  }
} catch (error) {
  if (!(error instanceof ItemError)) throw error;
  console.error(error.message);
  process.exit(1);
}
