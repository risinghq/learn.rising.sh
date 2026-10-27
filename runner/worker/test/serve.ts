import http from "node:http";

import { start } from "./harness.ts";

// A local Worker with the fake provider for the browser tests.
// It prints the origins of the site and of the control, and serves until SIGTERM.
// The control listens only on 127.0.0.1 and exposes the fake consent and
// the row counts of the database.
const TABLES = [
  "users",
  "identities",
  "sessions",
  "lesson_done",
  "exercise_state",
  "kv",
];

const harness = await start();
const site = await harness.origin();

const control = http.createServer(async (req, res) => {
  const send = (status: number, body: unknown) => {
    res
      .writeHead(status, { "content-type": "application/json" })
      .end(JSON.stringify(body));
  };
  try {
    if (req.method === "GET" && req.url === "/rows") {
      const rows: Record<string, number> = {};
      for (const table of TABLES) {
        const count = await harness.db
          .prepare(`SELECT COUNT(*) AS n FROM ${table}`)
          .first<number>("n");
        rows[table] = count ?? 0;
      }
      return send(200, rows);
    }
    if (req.method === "POST" && req.url === "/consent") {
      let text = "";
      for await (const chunk of req) text += chunk;
      const { authorizeUrl, subject } = JSON.parse(text);
      return send(200, {
        code: harness.provider.consent(authorizeUrl, subject),
      });
    }
    send(404, { error: "no existe" });
  } catch (error) {
    send(500, { error: String(error) });
  }
});
await new Promise<void>((ready) => control.listen(0, "127.0.0.1", ready));
const { port } = control.address() as { port: number };
console.log(JSON.stringify({ site, control: `http://127.0.0.1:${port}` }));

process.on("SIGTERM", async () => {
  control.close();
  await harness.dispose();
  process.exit(0);
});
