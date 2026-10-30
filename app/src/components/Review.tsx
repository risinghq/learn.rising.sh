import { Check, X } from "lucide-react";
import { useEffect, useId, useMemo, useState } from "react";

import { courseKey, readJson } from "@site/progress.ts";

import type { Lesson } from "../model.ts";
import {
  answered,
  dueQuestions,
  numericRight,
  PER_DAY,
  type NumericAsk,
  type Question,
  type ReviewState,
} from "../review.ts";
import { save, useReady } from "../store.ts";
import { Rich } from "./Rich.tsx";

interface Loaded {
  questions: Question[];
  total: number;
}

async function load(
  slug: string,
  lessons: Lesson[],
  key: string,
): Promise<Loaded> {
  const files = await Promise.all(
    lessons.map((lesson) =>
      fetch(`/${slug}/lessons/${lesson.id}/lesson.json`).then(
        async (resp) => ({ lesson, file: await resp.json() }),
        () => undefined,
      ),
    ),
  );
  const due = dueQuestions(
    files.filter((f) => f !== undefined),
    readJson<ReviewState>(key, {}),
    Date.now(),
    Math.random,
  );
  return { questions: due.slice(0, PER_DAY), total: due.length };
}

function Question({
  question,
  storeKey,
}: {
  question: Question;
  storeKey: string;
}) {
  const { ask } = question;
  const [result, setResult] = useState<{
    chosen?: number;
    correct: boolean;
    days: number;
  }>();
  const [text, setText] = useState("");
  const input = useId();

  const answer = (correct: boolean, chosen?: number) => {
    const next = answered(
      readJson<ReviewState>(storeKey, {}),
      question.id,
      correct,
      Date.now(),
    );
    save(storeKey, next.state);
    setResult({ chosen, correct, days: next.days });
  };
  const check = (numeric: NumericAsk) => {
    const correct = numericRight(numeric, text);
    if (correct !== undefined && !result) answer(correct);
  };

  return (
    <li className="rq">
      <p className="from">
        {question.lesson.section} {question.lesson.title}
      </p>
      <p className="prompt">
        <Rich text={ask.prompt} />
      </p>
      {ask.kind === "choice" ? (
        <div className="opts">
          {ask.options.map((option, k) => {
            const right = k === ask.right;
            const state =
              result && (right ? "ok" : k === result.chosen ? "no" : undefined);
            return (
              <button
                key={k}
                type="button"
                className="opt"
                data-state={state}
                disabled={result !== undefined}
                onClick={() => answer(right, k)}
              >
                <Rich text={option} />
                {state === "ok" ? (
                  <Check aria-hidden="true" />
                ) : state === "no" ? (
                  <X aria-hidden="true" />
                ) : null}
                {state ? (
                  <span className="sr">
                    {state === "ok" ? " (correcta)" : " (tu respuesta)"}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      ) : (
        <form
          className="num-answer"
          onSubmit={(e) => {
            e.preventDefault();
            check(ask);
          }}
        >
          <label className="sr" htmlFor={input}>
            Tu respuesta
          </label>
          <input
            id={input}
            inputMode="decimal"
            placeholder="Tu respuesta"
            value={text}
            readOnly={result !== undefined}
            onChange={(e) => setText(e.target.value)}
          />
          <button type="submit" className="btn" disabled={result !== undefined}>
            Comprobar
          </button>
        </form>
      )}
      <div className="fb" role="status">
        {result ? (
          <>
            <b>{result.correct ? "Correcto." : "Incorrecto."}</b>{" "}
            <Rich
              text={
                (result.correct ? ask.why : ask.hint) ||
                (result.correct ? "" : "Volverá mañana.")
              }
            />
            <span className="when">
              Próximo repaso en {result.days}{" "}
              {result.days === 1 ? "día" : "días"}.
            </span>
          </>
        ) : null}
      </div>
    </li>
  );
}

export function Review({
  slug,
  lessons,
  done,
}: {
  slug: string;
  lessons: Lesson[];
  done: ReadonlySet<string>;
}) {
  const ready = useReady();
  const key = courseKey(slug, "repaso");
  const finished = useMemo(
    () => lessons.filter((l) => done.has(l.id)),
    [lessons, done],
  );
  const [loaded, setLoaded] = useState<Loaded>();
  const ids = finished.map((l) => l.id).join();

  useEffect(() => {
    if (!ready || finished.length === 0) return;
    let live = true;
    void load(slug, finished, key).then((result) => live && setLoaded(result));
    return () => {
      live = false;
    };
  }, [ready, ids]);

  if (finished.length === 0) return null;
  return (
    <section className="review" aria-labelledby="t-repaso">
      <h2 id="t-repaso">Repaso de hoy</h2>
      {loaded === undefined ? null : loaded.questions.length === 0 ? (
        <p className="muted">Nada que repasar hoy. Vuelve mañana.</p>
      ) : (
        <>
          <p className="muted num">
            {loaded.questions.length} de {loaded.total} pendientes
          </p>
          <ol className="questions">
            {loaded.questions.map((q) => (
              <Question key={q.id} question={q} storeKey={key} />
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
