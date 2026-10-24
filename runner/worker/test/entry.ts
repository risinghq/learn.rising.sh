import { DurableObject } from "cloudflare:workers";

import real, { Budget as RealBudget } from "../src/index.ts";

// Sustituye la imagen por un contenedor falso que registra las cabeceras, nunca
// el cuerpo, y responde con el contrato de /run.
export { RateLimiter } from "../src/index.ts";

// Un Budget real cuyo almacenamiento falla al ajustar el coste cuando la prueba
// lo pide con la variable FAKE_SETTLE_FAILS.
export class Budget extends RealBudget {
  override async settle(
    ...args: Parameters<RealBudget["settle"]>
  ): Promise<number> {
    if ((this.env as { FAKE_SETTLE_FAILS?: string }).FAKE_SETTLE_FAILS) {
      throw new Error("StorageDown: el almacenamiento no responde");
    }
    return super.settle(...args);
  }
}

interface TestEnv {
  // Instancias que elige el Worker, en orden, separadas por comas ("0,1").
  FAKE_PICKS?: string;
  INSTANCES: string;
  // Fecha ISO en que se detiene el reloj. Solo avanza con /clock?advance=<ms> y con
  // el trabajo del corredor falso ("TRABAJO-<ms>").
  FAKE_CLOCK?: string;
}

let picked = false;
let frozen: number | undefined;

function freeze(env: TestEnv): void {
  if (!env.FAKE_CLOCK || frozen !== undefined) return;
  frozen = Date.parse(env.FAKE_CLOCK);
  Date.now = () => frozen!;
}

// El corredor repite en `stdout`, en el `message` de los casos y en `error` lo que
// recibió: así las pruebas ven si el Worker deja pasar algo de eso a la base.
// La palabra que contiene el código decide el resultado.
function answer(code: string) {
  const base = {
    stdout: code,
    error: null,
    tests: [] as unknown[],
    ms: 42,
    killed: null,
    peak_mb: 1,
  };
  if (code.includes("FALLA")) {
    return {
      ...base,
      passed: false,
      tests: [
        {
          name: "n = 2, 3 y 4",
          visible: true,
          passed: false,
          message: `salió ${code}`,
        },
        { name: "caso oculto 1", visible: false, passed: false, message: code },
        { name: "otro caso", visible: true, passed: true, message: "" },
      ],
    };
  }
  if (code.includes("ERROR-RARO")) {
    return { ...base, passed: false, error: `algo raro pasó con ${code}` };
  }
  if (code.includes("ERROR")) {
    return {
      ...base,
      passed: false,
      error: `NameError: name 'x' is not defined (línea 1: ${code})`,
    };
  }
  if (code.includes("MATADO")) {
    return {
      ...base,
      passed: false,
      error: `tiempo agotado: ${code}`,
      killed: "time",
    };
  }
  return {
    ...base,
    passed: true,
    stdout: `recibidos ${code.length} caracteres\n`,
  };
}

export default {
  async fetch(
    request: Request,
    env: TestEnv,
    ctx: ExecutionContext,
  ): Promise<Response> {
    const runners = (
      ctx as unknown as { exports: { Runner: DurableObjectNamespace } }
    ).exports.Runner;
    freeze(env);
    const url = new URL(request.url);
    if (url.pathname === "/clock") {
      frozen = (frozen ?? Date.now()) + Number(url.searchParams.get("advance"));
      return Response.json({ now: frozen });
    }
    // Otro alumno que ya tiene un trabajo en la instancia 0, sin pasar por el Worker.
    if (url.pathname === "/other-learner") {
      return runners.get(runners.idFromName("instance-0")).fetch(
        new Request("http://runner/run", {
          method: "POST",
          body: JSON.stringify({ code: "ajeno" }),
        }),
      );
    }
    if (env.FAKE_PICKS && !picked) {
      picked = true;
      const picks = env.FAKE_PICKS.split(",").map(Number);
      // getRandom elige con Math.random: así la prueba decide qué instancia toca.
      Math.random = () => ((picks.shift() ?? 0) + 0.5) / Number(env.INSTANCES);
    }
    return real.fetch(request, env as never, ctx);
  },
  scheduled: (controller: ScheduledController, env: never) =>
    real.scheduled(controller, env),
};

export class Runner extends DurableObject {
  // Verdadero mientras la instancia atiende el trabajo de otro alumno.
  private busy = false;
  private killed = false;

  async fetch(request: Request): Promise<Response> {
    const headers = [...request.headers.keys()].toSorted();
    console.log(
      `FAKE_RUNNER_CALL ${JSON.stringify({ path: new URL(request.url).pathname, headers })}`,
    );
    const { code } = (await request.json()) as { code: string };
    if (code === "romper-contenedor")
      throw new Error("ContainerDown: la instancia se cayó");
    if (code === "ajeno") {
      this.busy = true;
      this.killed = false;
      await scheduler.wait(900);
      this.busy = false;
      if (this.killed)
        throw new Error("ContainerKilled: la instancia se detuvo");
    } else if (this.busy) {
      // Como runner/server.py: sin ranura libre responde 503 y no espera.
      return Response.json({ error: "ocupado" }, { status: 503 });
    } else {
      // Un trabajo que no termina a tiempo: solo el Worker puede cortarlo.
      await scheduler.wait(code === "colgar" ? 1500 : 15);
      // Un trabajo que dura tanto como dice el código, en el reloj detenido.
      const work = /TRABAJO-(\d+)/.exec(code);
      if (work && frozen !== undefined) frozen += Number(work[1]);
    }
    return Response.json(answer(code));
  }

  // Container.destroy() mata la instancia.
  async destroy(): Promise<void> {
    if (this.busy) this.killed = true;
    console.log("FAKE_RUNNER_STOP");
  }
}
