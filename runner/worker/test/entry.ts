import { DurableObject } from "cloudflare:workers";

import real, { Budget as RealBudget } from "../src/index.ts";

// Replaces the image with a fake container that logs the headers, never the
// body, and answers with the /run contract.
export { RateLimiter } from "../src/index.ts";

// A real Budget whose storage fails when adjusting the cost if the test asks
// for it with the FAKE_SETTLE_FAILS variable.
export class Budget extends RealBudget {
  override async settle(
    ...args: Parameters<RealBudget["settle"]>
  ): Promise<number> {
    if ((this.env as { FAKE_SETTLE_FAILS?: string }).FAKE_SETTLE_FAILS) {
      throw new Error("StorageDown: the storage does not answer");
    }
    return super.settle(...args);
  }
}

interface TestEnv {
  // ISO date at which the clock stops. It advances only with /clock?advance=<ms>
  // and with the fake runner's job ("TRABAJO-<ms>").
  FAKE_CLOCK?: string;
}

let frozen: number | undefined;

function freeze(env: TestEnv): void {
  if (!env.FAKE_CLOCK || frozen !== undefined) return;
  frozen = Date.parse(env.FAKE_CLOCK);
  Date.now = () => frozen!;
}

// The runner repeats what it received in `stdout`, in the `message` of the cases
// and in `error`, so the tests see whether the Worker lets any of it reach the
// database. The word the code contains decides the result. The reply texts
// imitate the real runner's, which are in Spanish.
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
    // Another learner who already has a job on instance 0, without going through the Worker.
    if (url.pathname === "/other-learner") {
      return runners.get(runners.idFromName("instance-0")).fetch(
        new Request("http://runner/run", {
          method: "POST",
          body: JSON.stringify({ code: "ajeno" }),
        }),
      );
    }
    return real.fetch(request, env as never, ctx);
  },
  scheduled: (controller: ScheduledController, env: never) =>
    real.scheduled(controller, env),
};

export class Runner extends DurableObject {
  // True while the instance serves another learner's job.
  private busy = false;
  private killed = false;

  async fetch(request: Request): Promise<Response> {
    const headers = [...request.headers.keys()].toSorted();
    console.log(
      `FAKE_RUNNER_CALL ${JSON.stringify({ path: new URL(request.url).pathname, headers, instance: this.ctx.id.name })}`,
    );
    const { code } = (await request.json()) as { code: string };
    if (code === "romper-contenedor")
      throw new Error("ContainerDown: the instance went down");
    if (code === "ajeno") {
      this.busy = true;
      this.killed = false;
      await scheduler.wait(900);
      this.busy = false;
      if (this.killed)
        throw new Error("ContainerKilled: the instance was stopped");
    } else if (this.busy) {
      // Like runner/server.py: with no free slot it answers 503 and does not wait.
      return Response.json({ error: "ocupado" }, { status: 503 });
    } else {
      // A job that does not finish in time: only the Worker can cut it off.
      await scheduler.wait(code === "colgar" ? 1500 : 15);
      // A job that lasts as long as the code says, on the stopped clock.
      const work = /TRABAJO-(\d+)/.exec(code);
      if (work && frozen !== undefined) frozen += Number(work[1]);
    }
    return Response.json(answer(code));
  }

  // Container.destroy() kills the instance.
  async destroy(): Promise<void> {
    if (this.busy) this.killed = true;
    console.log("FAKE_RUNNER_STOP");
  }
}
