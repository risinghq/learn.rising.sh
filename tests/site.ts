import { resolve, sep } from "node:path";

const SITE = resolve(import.meta.dirname, "..", "site");

export interface SiteServer {
  base: string;
  stop: () => Promise<void>;
}

export function serveSite(lessonJsonDelayMs = 0): SiteServer {
  const server = Bun.serve({
    hostname: "127.0.0.1",
    port: 0,
    async fetch(request) {
      const { pathname } = new URL(request.url);
      if (lessonJsonDelayMs && pathname.endsWith("/lesson.json")) {
        await Bun.sleep(lessonJsonDelayMs);
      }
      const path = resolve(
        SITE,
        `.${decodeURIComponent(pathname)}${pathname.endsWith("/") ? "index.html" : ""}`,
      );
      const file = Bun.file(path);
      if (!path.startsWith(SITE + sep) || !(await file.exists())) {
        return new Response("Not found", { status: 404 });
      }
      return new Response(file);
    },
  });
  return {
    base: `http://127.0.0.1:${server.port}`,
    stop: () => server.stop(true),
  };
}
