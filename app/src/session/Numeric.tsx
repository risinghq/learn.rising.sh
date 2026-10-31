import { Delete } from "lucide-react";
import { useState } from "react";

import { grade, parseNumber } from "../../../drill/grade.ts";
import { Rich } from "../components/Rich.tsx";
import type { ItemProps } from "./props.ts";

const KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", ",", "0"];
const MAX_LENGTH = 9;

export function Numeric({ item, given, onAnswer }: ItemProps<"numeric">) {
  const [text, setText] = useState("");
  const locked = given !== undefined;
  const shown = locked ? String(given) : text;
  const valid = Number.isFinite(parseNumber(text));

  const press = (key: string) =>
    setText((current) => {
      if (current.length >= MAX_LENGTH) return current;
      if (key === "," && current.includes(",")) return current;
      return current + key;
    });

  return (
    <>
      <p className="prompt">
        <Rich text={item.prompt} />
      </p>
      <output
        className="readout num"
        data-state={
          locked ? (grade(item, given).correct ? "ok" : "no") : undefined
        }
        aria-label="Tu respuesta"
      >
        {shown}
        {item.unit ? <span className="unit"> {item.unit}</span> : null}
      </output>
      {locked ? null : (
        <>
          <div className="keypad">
            {KEYS.map((key) => (
              <button
                key={key}
                type="button"
                className="key num"
                onClick={() => press(key)}
              >
                {key}
              </button>
            ))}
            <button
              type="button"
              className="key"
              aria-label="Borrar"
              disabled={text === ""}
              onClick={() => setText((current) => current.slice(0, -1))}
            >
              <Delete aria-hidden="true" />
            </button>
          </div>
          <button
            type="button"
            className="btn primary check"
            disabled={!valid}
            onClick={() => onAnswer(text)}
          >
            Comprobar
          </button>
        </>
      )}
    </>
  );
}
