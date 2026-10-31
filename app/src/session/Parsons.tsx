import { GripVertical } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { parsonsPool } from "../../../drill/present.ts";
import { Rich } from "../components/Rich.tsx";
import type { ItemProps } from "./props.ts";

function moved(order: number[], from: number, to: number): number[] {
  const copy = [...order];
  const [line] = copy.splice(from, 1);
  copy.splice(to, 0, line!);
  return copy;
}

export function Parsons({ item, given, onAnswer, seed }: ItemProps<"parsons">) {
  const pool = useMemo(() => parsonsPool(item, seed), [item, seed]);
  // `order` holds indexes into `pool`, so two equal lines stay apart.
  const [order, setOrder] = useState<number[]>([]);
  const [dragged, setDragged] = useState<number>();
  const list = useRef<HTMLOListElement>(null);
  const locked = given !== undefined;
  const loose = pool.map((_, k) => k).filter((k) => !order.includes(k));

  // The drag listens on the window: React may move the dragged row in the DOM, which would end a
  // pointer capture held by the row.
  useEffect(() => {
    if (dragged === undefined) return;
    const move = (e: PointerEvent) => {
      const rows = [...(list.current?.children ?? [])];
      const from = order.indexOf(dragged);
      // The row lands after every other row whose middle the pointer has passed.
      const target = rows.filter((row, k) => {
        const box = row.getBoundingClientRect();
        return k !== from && e.clientY > box.top + box.height / 2;
      }).length;
      if (target !== from) setOrder(moved(order, from, target));
    };
    const end = () => setDragged(undefined);
    addEventListener("pointermove", move);
    addEventListener("pointerup", end);
    addEventListener("pointercancel", end);
    return () => {
      removeEventListener("pointermove", move);
      removeEventListener("pointerup", end);
      removeEventListener("pointercancel", end);
    };
  }, [dragged, order]);

  return (
    <>
      <p className="prompt">
        <Rich text={item.prompt} />
      </p>
      {item.before ? (
        <pre className="code">
          <code>{item.before}</code>
        </pre>
      ) : null}
      <ol className="slots" ref={list} aria-label="Tu orden">
        {order.map((k, place) => {
          const state = locked
            ? pool[k] === item.lines[place]
              ? "ok"
              : "no"
            : undefined;
          return (
            <li
              key={k}
              className="slot"
              data-state={state}
              data-drag={dragged === k || undefined}
            >
              <button
                type="button"
                className="line"
                disabled={locked}
                onClick={() => setOrder(order.filter((j) => j !== k))}
              >
                <code>{pool[k]}</code>
              </button>
              {locked ? null : (
                <span
                  className="grip"
                  aria-hidden="true"
                  onPointerDown={(e) => {
                    e.preventDefault();
                    setDragged(k);
                  }}
                >
                  <GripVertical />
                </span>
              )}
            </li>
          );
        })}
        {order.length === 0 ? (
          <li className="slot" data-state="empty" aria-hidden="true" />
        ) : null}
      </ol>
      {locked ? null : (
        <>
          <ul className="pool" aria-label="Líneas">
            {loose.map((k) => (
              <li key={k}>
                <button
                  type="button"
                  className="line"
                  onClick={() => setOrder([...order, k])}
                >
                  <code>{pool[k]}</code>
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="btn primary check"
            disabled={order.length !== item.lines.length}
            onClick={() => onAnswer(order.map((k) => pool[k]!))}
          >
            Comprobar
          </button>
        </>
      )}
    </>
  );
}
