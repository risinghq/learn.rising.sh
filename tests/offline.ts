// Fails browser tests when a page requests an external address.
//
// Requests to 127.0.0.1 and localhost fall through to the test's own routes.
// Any other request is recorded and aborted, and `verify` exits 1 if any was.
import type {
  Browser,
  BrowserContext,
  BrowserContextOptions,
  Route,
} from "playwright";

const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost"]);

const external: string[] = [];

async function refuse(route: Route): Promise<void> {
  const url = route.request().url();
  if (LOCAL_HOSTS.has(new URL(url).hostname)) {
    await route.fallback();
    return;
  }
  external.push(url);
  console.error(`✗ request to an external host: ${url}`);
  await route.abort();
}

export async function newContext(
  browser: Browser,
  options: BrowserContextOptions = {},
): Promise<BrowserContext> {
  const context = await browser.newContext(options);
  await context.route("**/*", refuse);
  return context;
}

export function verify(): void {
  if (external.length) {
    const urls = [...new Set(external)]
      .toSorted()
      .map((url) => `  ${url}`)
      .join("\n");
    console.error(`The tests requested external addresses:\n${urls}`);
    process.exit(1);
  }
}
