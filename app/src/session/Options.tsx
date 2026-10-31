import { Check, X } from "lucide-react";

import { Rich } from "../components/Rich.tsx";

export function Options({
  options,
  chosen,
  right,
  mono,
  onPick,
}: {
  options: string[];
  chosen: number | undefined;
  right?: number;
  mono?: boolean;
  onPick: (index: number) => void;
}) {
  const locked = chosen !== undefined;
  return (
    <div className="opts">
      {options.map((option, k) => {
        const state = !locked
          ? undefined
          : right === undefined
            ? k === chosen
              ? "bet"
              : undefined
            : k === right
              ? "ok"
              : k === chosen
                ? "no"
                : undefined;
        return (
          <button
            key={option}
            type="button"
            className="opt"
            data-state={state}
            data-mono={mono || undefined}
            disabled={locked}
            onClick={() => onPick(k)}
          >
            {mono ? <code>{option}</code> : <Rich text={option} />}
            {state === "ok" ? (
              <Check aria-hidden="true" />
            ) : state === "no" ? (
              <X aria-hidden="true" />
            ) : null}
            {state ? (
              <span className="sr">
                {state === "ok"
                  ? " (correcta)"
                  : state === "no"
                    ? " (tu respuesta)"
                    : " (tu apuesta)"}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
