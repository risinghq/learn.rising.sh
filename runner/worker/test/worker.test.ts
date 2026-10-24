import { afterEach, describe, expect, it } from "vitest";

import {
  type Harness,
  type Options,
  FAIL_SECRET,
  SPENT_SECRET,
  TOKEN,
  VARS,
  clearOfMinuteEnd,
  start,
} from "./harness.ts";
import { signIn } from "./signin.ts";

const open: Harness[] = [];

async function worker(options?: Options): Promise<Harness> {
  const h = await start(options);
  open.push(h);
  return h;
}

afterEach(async () => {
  await Promise.all(open.splice(0).map((h) => h.dispose()));
});

const run = { code: "print(2 + 2)", mode: "run" };
const verified = { headers: { "x-turnstile-token": TOKEN } };

describe("GET /health", () => {
  it("responde sin llamar al contenedor", async () => {
    const h = await worker();
    const reply = await h.get("/health");
    expect(reply.status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(0);
  });
});

describe("el sitio y /run en un solo Worker", () => {
  it("sirve index.html en / sin llamar al contenedor", async () => {
    const h = await worker();
    const reply = await h.get("/");
    expect(reply.status).toBe(200);
    expect(reply.headers.get("content-type")).toContain("text/html");
    expect(reply.body).toContain("<title>");
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("sirve las lecciones y responde 404 a lo que no es un archivo", async () => {
    const h = await worker();
    expect((await h.get("/lesson.html")).status).toBe(200);
    expect((await h.get("/course.json")).body.parts).toBeDefined();
    expect((await h.get("/no-existe.html")).status).toBe(404);
  });

  it("ejecuta el código y devuelve el JSON del corredor con el token de prueba", async () => {
    const h = await worker();
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(200);
    expect(reply.body).toMatchObject({
      passed: true,
      error: null,
      tests: [],
      killed: null,
    });
    expect(reply.body.stdout).toBe("recibidos 12 caracteres\n");
    expect(reply.headers.get("set-cookie")).toContain("qg_session=");
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("responde 403 turnstile_missing con la clave del sitio cuando no hay token", async () => {
    const h = await worker();
    const reply = await h.post(run);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_missing");
    expect(reply.body.sitekey).toBe(VARS.TURNSTILE_SITE_KEY);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("responde 500 si falta la clave del sitio, porque la página no podría pasar Turnstile", async () => {
    const h = await worker({ vars: { TURNSTILE_SITE_KEY: "" } });
    const reply = await h.post(run);
    expect(reply.status).toBe(500);
    expect(reply.body.reason).toBe("internal_error");
    expect(reply.body.sitekey).toBeUndefined();
  });
});

describe("límite por IP", () => {
  it("responde 429 con Retry-After al pasar el límite por minuto", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "3" } });
    for (let i = 0; i < 3; i++)
      expect((await h.post(run, verified)).status).toBe(200);

    const reply = await h.post(run, verified);
    expect(reply.status).toBe(429);
    expect(reply.body.reason).toBe("rate_minute");
    expect(reply.body.error).toMatch(/Espera \d+ s/);
    const retryAfter = Number(reply.headers.get("retry-after"));
    expect(Number.isInteger(retryAfter)).toBe(true);
    expect(retryAfter).toBeGreaterThanOrEqual(1);
    expect(retryAfter).toBeLessThanOrEqual(60);
    expect(h.runnerCalls()).toHaveLength(3);
  });

  it("con peticiones simultáneas deja pasar exactamente el límite", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "3" } });
    const replies = await Promise.all(
      Array.from({ length: 10 }, () => h.post(run, verified)),
    );
    expect(replies.filter((reply) => reply.status === 200)).toHaveLength(3);
    expect(replies.filter((reply) => reply.status === 429)).toHaveLength(7);
  });

  it("cuenta cada IP por separado", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "1" } });
    expect(
      (await h.post(run, { ...verified, ip: "198.51.100.1" })).status,
    ).toBe(200);
    expect(
      (await h.post(run, { ...verified, ip: "198.51.100.1" })).status,
    ).toBe(429);
    expect(
      (await h.post(run, { ...verified, ip: "198.51.100.2" })).status,
    ).toBe(200);
  });

  it("responde 429 con Retry-After al pasar el límite del día", async () => {
    const h = await worker({ vars: { RATE_PER_DAY: "2" } });
    await h.post(run, verified);
    await h.post(run, verified);

    const reply = await h.post(run, verified);
    expect(reply.status).toBe(429);
    expect(reply.body.reason).toBe("rate_day");
    const retryAfter = Number(reply.headers.get("retry-after"));
    expect(retryAfter).toBeGreaterThanOrEqual(1);
    expect(retryAfter).toBeLessThanOrEqual(86_400);
    expect(h.runnerCalls()).toHaveLength(2);
  });

  it("limita también las peticiones que Turnstile rechaza", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "2" } });
    expect((await h.post(run)).status).toBe(403);
    expect((await h.post(run)).status).toBe(403);
    expect((await h.post(run)).status).toBe(429);
  });
});

describe("Turnstile", () => {
  it("responde 403 sin token y no llega al contenedor", async () => {
    const h = await worker();
    const reply = await h.post(run);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_missing");
    expect(h.runnerCalls()).toHaveLength(0);
    expect(h.siteverify.calls).toHaveLength(0);
  });

  it("responde 403 con un token que Turnstile rechaza", async () => {
    const h = await worker({ vars: { TURNSTILE_SECRET: FAIL_SECRET } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_failed");
    expect(reply.headers.get("set-cookie")).toBeNull();
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("responde 403 con un token ya usado", async () => {
    const h = await worker({ vars: { TURNSTILE_SECRET: SPENT_SECRET } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(403);
    expect(reply.body.reason).toBe("turnstile_failed");
  });

  it("responde 503 si Turnstile no responde", async () => {
    const h = await worker({ siteverify: "down" });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(503);
    expect(reply.body.reason).toBe("turnstile_unavailable");
    expect(reply.headers.get("retry-after")).toBe("10");
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("verifica una vez y luego deja pasar con la cookie de sesión", async () => {
    const h = await worker();
    const first = await h.post(run, verified);
    expect(first.status).toBe(200);
    expect(first.body.passed).toBe(true);
    const cookie = first.headers.get("set-cookie") ?? "";
    expect(cookie).toMatch(
      /^qg_session=\d+\.[0-9a-f]{64}; Max-Age=28800; Path=\/run; HttpOnly; Secure; SameSite=Strict$/,
    );

    const second = await h.post(run, {
      headers: { cookie: cookie.split(";")[0] },
    });
    expect(second.status).toBe(200);
    expect(second.headers.get("set-cookie")).toBeNull();
    expect(h.siteverify.calls).toHaveLength(1);
  });

  it("envía a Turnstile solo el secreto y el token", async () => {
    const h = await worker();
    await h.post(run, { ...verified, ip: "203.0.113.50" });
    expect(h.siteverify.calls).toHaveLength(1);
    expect(Object.keys(h.siteverify.calls[0]).toSorted()).toEqual([
      "response",
      "secret",
    ]);
  });

  it("rechaza una cookie manipulada, ajena a la IP o caducada", async () => {
    const h = await worker({ vars: { SESSION_HOURS: "0.00001" } });
    const issued =
      (await h.post(run, verified)).headers.get("set-cookie") ?? "";
    const cookie = issued.split(";")[0];
    const tag = cookie.slice(-64);

    const forged = cookie.replace(tag, "0".repeat(64));
    expect((await h.post(run, { headers: { cookie: forged } })).status).toBe(
      403,
    );

    const other = await h.post(run, {
      ip: "198.51.100.99",
      headers: { cookie },
    });
    expect(other.status).toBe(403);

    await new Promise((resolve) => setTimeout(resolve, 150));
    const expired = await h.post(run, { headers: { cookie } });
    expect(expired.status).toBe(403);
    expect(expired.body.reason).toBe("turnstile_missing");
  });

  it("acepta la cookie mientras no caduca", async () => {
    const h = await worker();
    const cookie = (
      (await h.post(run, verified)).headers.get("set-cookie") ?? ""
    ).split(";")[0];
    expect((await h.post(run, { headers: { cookie } })).status).toBe(200);
  });
});

describe("tamaño del código", () => {
  const limit = 20_000;

  it("responde 413 sin llegar al contenedor", async () => {
    const h = await worker();
    const reply = await h.post(
      { code: "x".repeat(limit + 1), mode: "run" },
      verified,
    );
    expect(reply.status).toBe(413);
    expect(reply.body.reason).toBe("too_large");
    expect(reply.body.error).toContain("20000");
    expect(h.runnerCalls()).toHaveLength(0);
    expect(h.siteverify.calls).toHaveLength(0);
  });

  it("cuenta bytes y no caracteres", async () => {
    const h = await worker();
    const code = "é".repeat(limit / 2 + 1);
    expect(code).toHaveLength(limit / 2 + 1);
    expect((await h.post({ code, mode: "run" }, verified)).status).toBe(413);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("deja pasar un código de exactamente el máximo", async () => {
    const h = await worker();
    const reply = await h.post(
      { code: "x".repeat(limit), mode: "run" },
      verified,
    );
    expect(reply.status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("responde 413 a un cuerpo enorme sin leerlo entero", async () => {
    const h = await worker();
    // Solo el encabezado: el 413 llega sin que el cuerpo se haya enviado.
    const status = await h.declare("POST", "/run", 6 * limit + 1025, {
      ...verified.headers,
      "content-type": "application/json",
    });
    expect(status).toBe(413);
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("responde 400 a un JSON inválido o sin código", async () => {
    const h = await worker();
    expect(
      (await h.post(null, { ...verified, raw: "{no es json" })).status,
    ).toBe(400);
    expect((await h.post({ mode: "run" }, verified)).status).toBe(400);
    expect((await h.post({ code: 3 }, verified)).status).toBe(400);
    expect(h.runnerCalls()).toHaveLength(0);
  });
});

// Los precios de las pruebas son los de `standard-2` con `sleepAfter` de 60 s:
// 20 000 nanodólares por segundo de CPU y 15 840 por segundo encendida (6 GiB y
// 12 GB). Una ejecución aislada de 2 s cuesta 2 × 20 000 de CPU y 62 × 15 840 de
// instancia encendida, que son 1 022 080. Reservar una ejecución aislada aparta
// 30 × 20 000 + 90 × 15 840 = 2 025 600.
const CLOCK = "2026-10-15T12:00:00Z";
const ISOLATED_2S = 1_022_080;

const work = (ms: number) => ({ code: `TRABAJO-${ms}`, mode: "run" });

function costs(h: Harness): number[] {
  return h
    .workerLogs()
    .map((line) => JSON.parse(line))
    .filter((line) => line.event === "run" && line.cost_nano_usd !== undefined)
    .map((line) => line.cost_nano_usd);
}

describe("presupuesto mensual", () => {
  // Con una reserva de 0,05 s una ejecución que se cuelga se detiene a los 50 ms;
  // sin tope costaría los 1500 ms que tarda.
  const hang = { code: "colgar", mode: "run" };

  it("cobra la ventana encendida de una ejecución aislada y solo la ampliación de la siguiente", async () => {
    // Instancias elegidas: 0, 0, 1 y 0.
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, FAKE_PICKS: "0,0,1,0" },
    });
    await h.post(work(2000), verified);
    // Dentro de la ventana de la primera: 1 s de CPU y el segundo que alarga la
    // ventana encendida (1 × 20 000 + 1 × 15 840).
    await h.post(work(1000), verified);
    // Otra instancia no comparte la ventana.
    await h.post(work(2000), verified);
    // Pasada la ventana, la instancia 0 se apagó y vuelve a cobrar entera.
    await h.advance(600_000);
    await h.post(work(2000), verified);

    expect(costs(h)).toEqual([ISOLATED_2S, 35_840, ISOLATED_2S, ISOLATED_2S]);
  });

  it.each([
    { type: "lite", nano: 49_930 },
    { type: "standard-1", nano: 674_720 },
    { type: "standard-2", nano: ISOLATED_2S },
    { type: "standard-4", nano: 2_106_800 },
  ])("el precio sale del tipo de instancia: $type", async ({ type, nano }) => {
    const h = await worker({
      vars: { FAKE_CLOCK: CLOCK, INSTANCE_TYPE: type },
    });
    await h.post(work(2000), verified);
    expect(costs(h)).toEqual([nano]);
  });

  it("responde 500 con un tipo de instancia que no existe", async () => {
    const h = await worker({ vars: { INSTANCE_TYPE: "gigante" } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(500);
    expect(h.workerLogs().join("\n")).toContain("INSTANCE_TYPE");
  });

  it("detiene una ejecución que pasa de lo apartado y no cobra más que la reserva", async () => {
    // La reserva son 0,05 × 20 000 de CPU y 60,05 × 15 840 de instancia encendida.
    const reserved = 952_192;
    const h = await worker({
      vars: { RESERVED_BUSY_SECONDS: "0.05", FAKE_PICKS: "0" },
    });
    const reply = await h.post(hang, verified);
    expect(reply.status).toBe(504);
    expect(reply.body.reason).toBe("run_too_long");
    expect(h.runnerStops()).toBe(1);

    const line = h
      .workerLogs()
      .map((entry) => JSON.parse(entry))
      .find((entry) => entry.outcome === "run_too_long");
    expect(line.busy_ms).toBeLessThan(1000);
    // Lo cobrado es la ventana apartada, no la que habría durado el trabajo.
    expect(line.cost_nano_usd).toBeLessThanOrEqual(reserved);
    expect(line.cost_nano_usd).toBeGreaterThan(900_000);
  });

  it("al llegar al tope solo detiene la instancia de la petición, no la que atiende a otro alumno", async () => {
    // El primer intento cae en la instancia 0, que atiende a otro alumno y responde
    // 503; el reintento cae en la 1, donde el trabajo se cuelga.
    const h = await worker({
      vars: { RESERVED_BUSY_SECONDS: "0.4", FAKE_PICKS: "0,1" },
    });
    const other = h.get("/other-learner");
    while (h.runnerCalls().length < 1)
      await new Promise((resolve) => setTimeout(resolve, 10));

    const reply = await h.post(hang, verified);
    expect(reply.status).toBe(504);
    expect(reply.body.reason).toBe("run_too_long");
    // El trabajo ajeno, el primer intento (503) y el reintento.
    expect(h.runnerCalls()).toHaveLength(3);
    expect(h.runnerStops()).toBe(1);

    const finished = await other;
    expect(finished.status).toBe(200);
    expect(finished.body.passed).toBe(true);
  });

  it("no ejecuta si la reserva de una ejecución ya no cabe", async () => {
    // Con 0,001 USD el público dispone de 750 000 nanodólares y la reserva de una
    // ejecución aislada son 2 025 600.
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.001" } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(503);
    expect(reply.body.reason).toBe("budget");
    expect(reply.body.error).toContain("mes");
    expect(h.runnerCalls()).toHaveLength(0);
  });

  it("con sitio para una sola ejecución, de varias simultáneas solo una llega al contenedor", async () => {
    // El público dispone de 2 100 000 nanodólares: cabe una reserva aislada
    // (2 025 600) y ninguna otra, ni en su instancia ni en la contigua.
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.0028" } });
    const replies = await Promise.all(
      Array.from({ length: 8 }, () => h.post(run, verified)),
    );

    expect(replies.filter((reply) => reply.status === 200)).toHaveLength(1);
    const refused = replies.filter((reply) => reply.status === 503);
    expect(refused).toHaveLength(7);
    for (const reply of refused) expect(reply.body.reason).toBe("budget");
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("al terminar cambia la reserva por el coste medido y deja sitio a la siguiente", async () => {
    // El público dispone de 3 000 000 de nanodólares. Cada ejecución en su
    // instancia aparta 2 025 600 y la primera gasta 950 400 (el reloj no avanza):
    // la segunda solo cabe si la primera devolvió lo que no gastó.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.004",
        FAKE_CLOCK: CLOCK,
        FAKE_PICKS: "0,1",
      },
    });
    expect((await h.post(run, verified)).status).toBe(200);
    expect((await h.post(run, verified)).status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(2);
    expect(costs(h)).toEqual([950_400, 950_400]);
  });

  it("devuelve la reserva si Turnstile rechaza la petición", async () => {
    // El público dispone de 2 250 000 nanodólares: cabe una reserva y no dos.
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.003" } });
    for (let i = 0; i < 3; i++) expect((await h.post(run)).status).toBe(403);
    expect((await h.post(run, verified)).status).toBe(200);
  });

  it("no gasta una verificación de Turnstile cuando ya no hay presupuesto", async () => {
    const h = await worker({ vars: { MONTHLY_BUDGET_USD: "0.001" } });
    expect((await h.post(run, verified)).status).toBe(503);
    expect(h.siteverify.calls).toHaveLength(0);
  });

  it("sigue ejecutando mientras el gasto está bajo el presupuesto", async () => {
    const h = await worker();
    for (let i = 0; i < 5; i++)
      expect((await h.post(run, verified)).status).toBe(200);
    expect(h.runnerCalls()).toHaveLength(5);
  });

  it("un fallo al registrar el coste no cambia la respuesta de una ejecución correcta", async () => {
    const h = await worker({ vars: { FAKE_SETTLE_FAILS: "1" } });
    const reply = await h.post(run, verified);
    expect(reply.status).toBe(200);
    expect(reply.body.passed).toBe(true);
    const lines = h.workerLogs().map((line) => JSON.parse(line));
    expect(lines.filter((line) => line.where === "settle")).toHaveLength(1);
  });

  it("un fallo al registrar el coste no tapa el error del contenedor", async () => {
    const h = await worker({ vars: { FAKE_SETTLE_FAILS: "1" } });
    const reply = await h.post({ code: "romper-contenedor" }, verified);
    expect(reply.status).toBe(500);
    expect(reply.body.reason).toBe("internal_error");
    // Quedan dos líneas: la del ajuste fallido y la del error de la petición.
    const lines = h.workerLogs().map((line) => JSON.parse(line));
    expect(lines.filter((line) => line.where === "settle")).toHaveLength(1);
    expect(
      lines.filter((line) => line.outcome === "internal_error" && !line.where),
    ).toHaveLength(1);
  });
});

describe("topes del presupuesto", () => {
  const MAINTAINER = "1001";

  async function maintainer(h: Harness) {
    const { cookie } = await signIn(h, "github", MAINTAINER);
    return { headers: { cookie: cookie! } };
  }

  it("el público para al 75 % del presupuesto y un mantenedor sigue hasta el 100 %", async () => {
    // El público dispone de 3 075 000 de los 4 100 000 nanodólares. Una ejecución
    // aislada de 2 s gasta 1 022 080 y la reserva de la siguiente cabe (3 047 680);
    // otra en la instancia 0 aparta 1 106 880 más, que pasa del 75 % y no del total.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.0041",
        MAINTAINERS: MAINTAINER,
        FAKE_CLOCK: CLOCK,
        FAKE_PICKS: "0,1,0,0,0",
      },
    });
    const staff = await maintainer(h);
    expect((await h.post(work(2000), verified)).status).toBe(200);
    expect((await h.post(work(2000), verified)).status).toBe(200);

    const refused = await h.post(work(1000), verified);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget");

    const allowed = await h.post(work(1000), staff);
    expect(allowed.status).toBe(200);
    expect(h.siteverify.calls).toHaveLength(2);
    // 1 s de CPU y los 3 s que alargan la ventana de la instancia 0.
    expect(costs(h)).toEqual([ISOLATED_2S, ISOLATED_2S, 67_520]);

    // Empieza otro mes: el público vuelve a ejecutar.
    await h.advance(20 * 86_400_000);
    expect((await h.post(work(1000), verified)).status).toBe(200);
  });

  it("el público para en su tope diario, un mantenedor no, y al día siguiente vuelve", async () => {
    // 1/10 de los 30 000 000 del público son 3 000 000 al día: cabe una ejecución
    // aislada (1 022 080 gastados) y la reserva de otra (2 025 600) ya no.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.04",
        PUBLIC_BUDGET_DAYS: "10",
        MAINTAINERS: MAINTAINER,
        FAKE_CLOCK: CLOCK,
        FAKE_PICKS: "0,1,1,1",
      },
    });
    const staff = await maintainer(h);
    expect((await h.post(work(2000), verified)).status).toBe(200);

    const refused = await h.post(work(2000), verified);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget_day");
    expect(refused.body.error).toContain("hoy");
    // Faltan 12 h menos los 2 s de la ejecución para la medianoche UTC.
    expect(refused.headers.get("retry-after")).toBe("43198");

    expect((await h.post(work(2000), staff)).status).toBe(200);

    await h.advance(13 * 3_600_000);
    expect((await h.post(work(2000), verified)).status).toBe(200);
  });

  it("al llegar al 100 % ni un mantenedor ejecuta", async () => {
    // Una ejecución aislada gasta 950 400 y la siguiente aparta 2 025 600: 2 976 000
    // pasan de los 2 800 000 del presupuesto.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.0028",
        MAINTAINERS: MAINTAINER,
        FAKE_CLOCK: CLOCK,
        FAKE_PICKS: "0,1",
      },
    });
    const staff = await maintainer(h);
    expect((await h.post(run, staff)).status).toBe(200);

    const refused = await h.post(run, staff);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget");
    expect(h.runnerCalls()).toHaveLength(1);
  });

  it("si falla el ajuste el gasto se queda en lo apartado y solo puede sobrar", async () => {
    // Con el ajuste, dos ejecuciones aisladas gastan 950 400 y apartan 2 025 600:
    // 2 976 000 caben en los 3 000 000 del público. Sin él, la primera se queda
    // en 2 025 600 y la segunda ya no cabe.
    const h = await worker({
      vars: {
        MONTHLY_BUDGET_USD: "0.004",
        FAKE_SETTLE_FAILS: "1",
        FAKE_CLOCK: CLOCK,
        FAKE_PICKS: "0,1",
      },
    });
    expect((await h.post(run, verified)).status).toBe(200);
    const refused = await h.post(run, verified);
    expect(refused.status).toBe(503);
    expect(refused.body.reason).toBe("budget");
  });
});

describe("lo que recibe el contenedor", () => {
  it("solo el tipo del cuerpo: ni cookie, ni IP, ni token", async () => {
    const h = await worker();
    const first = await h.post(run, { ...verified, ip: "203.0.113.50" });
    const cookie = (first.headers.get("set-cookie") ?? "").split(";")[0];
    await h.post(run, {
      ip: "203.0.113.50",
      headers: { cookie, "user-agent": "prueba" },
    });

    const calls = h.runnerCalls();
    expect(calls).toHaveLength(2);
    for (const call of calls) {
      expect(call.path).toBe("/run");
      // content-length es solo el tamaño del cuerpo que el runtime añade al enviarlo.
      expect(call.headers.filter((name) => name !== "content-length")).toEqual([
        "content-type",
      ]);
    }
  });
});

describe("registro", () => {
  const MARK = "MARCA_SECRETA_DEL_CODIGO";
  const IP = "203.0.113.77";

  it("no guarda código, IP, token ni cookie en ningún camino", async () => {
    await clearOfMinuteEnd();
    const h = await worker({ vars: { RATE_PER_MINUTE: "5" } });
    const code = `print("${MARK}")`;
    const cookie = (
      (
        await h.post(
          { code, mode: "check", exercise: "p1-quickstart/ghz" },
          { ...verified, ip: IP },
        )
      ).headers.get("set-cookie") ?? ""
    ).split(";")[0];

    await h.post(
      { code, mode: "check", exercise: "p1-quickstart/ghz" },
      { ip: IP, headers: { cookie } },
    );
    await h.post(
      { code: code + "x".repeat(20_000) },
      { ip: IP, headers: { cookie } },
    );
    await h.post(null, {
      ip: IP,
      headers: { cookie },
      raw: `{"code": "${MARK}`,
    });
    await h.post({ code, mode: MARK, exercise: `${MARK}/${MARK}` }, { ip: IP });
    const limited = await h.post({ code }, { ip: IP, headers: { cookie } });
    expect(limited.status).toBe(429);

    const lines = h.workerLogs();
    expect(lines.length).toBeGreaterThanOrEqual(6);
    const everything = lines.join("\n");
    for (const secret of [
      MARK,
      IP,
      TOKEN,
      cookie.split("=")[1],
      "198.51.100",
    ]) {
      expect(everything).not.toContain(secret);
    }
    for (const line of lines) {
      const entry = JSON.parse(line);
      expect(entry.event).toBe("run");
      expect(
        Object.keys(entry).every((key) =>
          [
            "event",
            "outcome",
            "status",
            "mode",
            "exercise",
            "code_bytes",
            "busy_ms",
            "cost_nano_usd",
          ].includes(key),
        ),
      ).toBe(true);
    }
  });

  it("una petición aceptada deja una línea con el resultado y el coste", async () => {
    const h = await worker();
    await h.post(
      { code: "print(1)", mode: "check", exercise: "p1-quickstart/ghz" },
      verified,
    );
    const [line] = h.workerLogs();
    expect(JSON.parse(line)).toMatchObject({
      event: "run",
      outcome: "ok",
      status: 200,
      mode: "check",
      exercise: "p1-quickstart/ghz",
      code_bytes: 8,
    });
    expect(JSON.parse(line).cost_nano_usd).toBeGreaterThan(0);
  });

  it("un error interno registra el nombre del error y no su texto", async () => {
    const h = await worker({
      vars: { RATE_PER_MINUTE: `no es un número ${MARK}` },
    });
    const reply = await h.post({ code: "print(1)" }, verified);
    expect(reply.status).toBe(500);
    const lines = h.workerLogs().join("\n");
    expect(lines).toContain("ConfigError");
    expect(lines).toContain("RATE_PER_MINUTE");
    expect(lines).not.toContain(MARK);
  });
});

describe("Turnstile real", async () => {
  // Cloudflare documenta estas claves de prueba. Esta prueba habla con su servicio.
  const reachable = await fetch(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    {
      method: "POST",
      body: new URLSearchParams({ secret: FAIL_SECRET, response: "x" }),
      signal: AbortSignal.timeout(5000),
    },
  ).then(
    () => true,
    () => false,
  );

  it.skipIf(!reachable)(
    "acepta con el secreto de prueba que siempre pasa",
    async () => {
      const h = await worker({ siteverify: "real" });
      expect((await h.post(run, verified)).status).toBe(200);
    },
  );

  it.skipIf(!reachable)(
    "rechaza con el secreto de prueba que siempre falla",
    async () => {
      const h = await worker({
        siteverify: "real",
        vars: { TURNSTILE_SECRET: FAIL_SECRET },
      });
      expect((await h.post(run, verified)).status).toBe(403);
    },
  );
});
