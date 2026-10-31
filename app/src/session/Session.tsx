import { Flame, Zap } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import {
  compactReviews,
  doneOf,
  PREF,
  readReviews,
  reviewKey,
} from "@site/progress.ts";

import { grade, type Answer } from "../../../drill/grade.ts";
import type { Bank, Item, ItemKind } from "../../../drill/item.ts";
import { planSession } from "../../../drill/schedule.ts";
import { awardXp, save, useReady, useStored, useXp } from "../store.ts";
import { Reminder } from "../components/Reminder.tsx";
import { Bug } from "./Bug.tsx";
import { Choice } from "./Choice.tsx";
import { Feedback } from "./Feedback.tsx";
import { Fill } from "./Fill.tsx";
import { Frame } from "./Frame.tsx";
import { Numeric } from "./Numeric.tsx";
import { Parsons } from "./Parsons.tsx";
import { Predict } from "./Predict.tsx";
import type { ItemProps } from "./props.ts";
import { answer, begin, finished, next, turnOf, type Run } from "./run.ts";

type Plan = Item[] | "failed" | undefined;

async function plan(slug: string): Promise<Item[]> {
  const resp = await fetch(`/${slug}/items.json`);
  if (!resp.ok) throw new Error(`${slug}/items.json: ${resp.status}`);
  const bank = (await resp.json()) as Bank;
  return planSession({
    bank: bank.items,
    log: readReviews(slug),
    done: doneOf(slug),
    now: Date.now(),
  });
}

function Question({
  item,
  ...rest
}: Omit<ItemProps<ItemKind>, "item"> & { item: Item }) {
  switch (item.kind) {
    case "choice":
      return <Choice item={item} {...rest} />;
    case "numeric":
      return <Numeric item={item} {...rest} />;
    case "predict":
      return <Predict item={item} {...rest} />;
    case "parsons":
      return <Parsons item={item} {...rest} />;
    case "fill":
      return <Fill item={item} {...rest} />;
    case "bug":
      return <Bug item={item} {...rest} />;
  }
}

function Done({ slug, run }: { slug: string; run: Run }) {
  const { streak } = useXp();
  const account = useStored(PREF.account);
  const asked = run.turns.filter((turn) => !turn.retry).length;
  return (
    <section className="done stage" aria-labelledby="t-done">
      <h1 id="t-done" className="gain num">
        <Zap aria-hidden="true" />
        <span className="sr">Repaso terminado. </span>+{run.xp} XP
      </h1>
      <p className="streak num">
        <Flame aria-hidden="true" data-active={streak > 0} />
        {streak} {streak === 1 ? "día" : "días"}
        <span className="sr"> de racha</span>
      </p>
      <p className="muted num">
        {run.first} de {asked} a la primera
      </p>
      {account === null ? (
        <section className="card keep" aria-labelledby="t-keep">
          <h2 id="t-keep">Guarda tu racha</h2>
          <div className="actions">
            <a className="btn" href={QGAccount.signInHref("google")}>
              Entrar con Google
            </a>
            <a className="btn" href={QGAccount.signInHref("github")}>
              Entrar con GitHub
            </a>
          </div>
        </section>
      ) : (
        <Reminder quiet />
      )}
      <a className="btn primary" href={`/${slug}/`}>
        Volver al camino
      </a>
    </section>
  );
}

function Play({ slug, items }: { slug: string; items: Item[] }) {
  const [run, setRun] = useState(() => begin(items));
  const [given, setGiven] = useState<Answer>();
  const started = useRef(Date.now());
  const saved = useRef(false);
  const turn = turnOf(run);
  const result =
    turn && given !== undefined ? grade(turn.item, given) : undefined;

  const over = finished(run);
  useEffect(() => {
    if (!over || saved.current) return;
    saved.current = true;
    save(
      reviewKey(slug),
      compactReviews([...readReviews(slug), ...run.reviews]),
    );
    if (run.xp > 0) {
      awardXp(run.xp);
      QGAccount.xp("drill", `${slug}:${started.current}`, run.xp);
    }
  }, [over, run, slug]);

  if (!turn) {
    return (
      <Frame
        slug={slug}
        progress={{ value: run.turns.length, max: run.turns.length }}
      >
        <Done slug={slug} run={run} />
      </Frame>
    );
  }
  const reply = (value: Answer) => {
    if (given !== undefined) return;
    setGiven(value);
    setRun(answer(run, grade(turn.item, value).correct, Date.now()));
  };
  return (
    <Frame slug={slug} progress={{ value: run.at, max: run.turns.length }}>
      <div className="stage" key={`${run.at}`}>
        <Question
          item={turn.item}
          given={given}
          onAnswer={reply}
          seed={`${started.current}:${run.at}`}
        />
      </div>
      <Feedback
        item={turn.item}
        result={result}
        last={run.at === run.turns.length - 1}
        onNext={() => {
          setRun(next(run));
          setGiven(undefined);
        }}
      />
    </Frame>
  );
}

export default function Session({ slug }: { slug: string }) {
  const ready = useReady();
  const [items, setItems] = useState<Plan>();
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!ready) return;
    let live = true;
    setItems(undefined);
    plan(slug).then(
      (planned) => live && setItems(planned),
      () => live && setItems("failed"),
    );
    return () => {
      live = false;
    };
  }, [ready, slug, attempt]);

  if (items === undefined)
    return (
      <Frame slug={slug}>
        <div className="stage">
          <p className="muted">Cargando…</p>
        </div>
      </Frame>
    );
  if (items === "failed")
    return (
      <Frame slug={slug}>
        <div className="stage">
          <p>No se pudieron cargar los ejercicios.</p>
          <button
            type="button"
            className="btn primary"
            onClick={() => setAttempt(attempt + 1)}
          >
            Reintentar
          </button>
        </div>
      </Frame>
    );
  if (items.length === 0)
    return (
      <Frame slug={slug}>
        <div className="stage">
          <p>Nada que repasar por ahora.</p>
          <a className="btn primary" href={`/${slug}/`}>
            Volver al camino
          </a>
        </div>
      </Frame>
    );
  return <Play slug={slug} items={items} />;
}
