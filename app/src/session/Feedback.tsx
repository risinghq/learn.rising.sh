import { Check, Dices, X } from "lucide-react";
import { useEffect, useRef } from "react";

import type { Result } from "../../../drill/grade.ts";
import type { Item } from "../../../drill/item.ts";
import { Rich } from "../components/Rich.tsx";

const number = (value: number) => String(value).replace(".", ",");

/** What the learner should have answered, for the items they missed. */
function correction(item: Item) {
  switch (item.kind) {
    case "choice":
      return <Rich text={item.options[item.right]!} />;
    case "fill":
      return <code>{item.options[item.right]}</code>;
    case "numeric":
      return (
        <b className="num">
          {number(item.answer)}
          {item.unit ? ` ${item.unit}` : ""}
        </b>
      );
    case "parsons":
      return (
        <pre className="code">
          <code>{item.lines.join("\n")}</code>
        </pre>
      );
    case "bug":
      return (
        <pre className="code">
          <code>{item.fix}</code>
        </pre>
      );
    case "predict":
      return null;
  }
}

/** The one line that says why: the grader's note for a miss, the item's own for the rest. */
function why(item: Item, result: Result): string | undefined {
  if (item.kind === "predict") return item.after;
  if (result.correct) return item.why;
  const note = result.feedback.replace(/^Incorrecto\.\s*/, "");
  return note || item.why;
}

export function Feedback({
  item,
  result,
  last,
  onNext,
}: {
  item: Item;
  result: Result | undefined;
  last: boolean;
  onNext: () => void;
}) {
  const next = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (result) next.current?.focus({ preventScroll: true });
  }, [result]);

  const bet = item.kind === "predict";
  const Icon = bet ? Dices : result?.correct ? Check : X;
  const note = result ? why(item, result) : undefined;
  return (
    <div
      className="dock"
      role="status"
      data-state={bet ? "bet" : result?.correct ? "ok" : "no"}
    >
      {result ? (
        <>
          <p className="verdict">
            <Icon aria-hidden="true" />
            {bet
              ? "Apuesta anotada"
              : result.correct
                ? "Correcto"
                : "Incorrecto"}
          </p>
          {!bet && !result.correct ? (
            <div className="reveal">{correction(item)}</div>
          ) : null}
          {note ? (
            <p className="why">
              <Rich text={note} />
            </p>
          ) : null}
          <button
            ref={next}
            type="button"
            className="btn primary"
            onClick={onNext}
          >
            {last ? "Terminar" : "Continuar"}
          </button>
        </>
      ) : null}
    </div>
  );
}
