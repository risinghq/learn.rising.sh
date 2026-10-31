import { Rich } from "../components/Rich.tsx";
import type { ItemProps } from "./props.ts";

export function Bug({ item, given, onAnswer }: ItemProps<"bug">) {
  const chosen = typeof given === "number" ? given : undefined;
  return (
    <>
      <p className="prompt">
        <Rich text={item.prompt} />
      </p>
      <ol className="lines">
        {item.lines.map((line, k) => {
          const state =
            chosen === undefined
              ? undefined
              : k === item.bug
                ? "ok"
                : k === chosen
                  ? "no"
                  : undefined;
          return (
            <li key={k}>
              <button
                type="button"
                className="line"
                data-state={state}
                disabled={chosen !== undefined}
                onClick={() => onAnswer(k)}
              >
                <span className="ln num" aria-hidden="true">
                  {k + 1}
                </span>
                <code>{line}</code>
                {state ? (
                  <span className="sr">
                    {state === "ok" ? " (el error)" : " (tu respuesta)"}
                  </span>
                ) : null}
              </button>
            </li>
          );
        })}
      </ol>
    </>
  );
}
