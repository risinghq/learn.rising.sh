import { BLANK } from "../../../drill/present.ts";
import { Rich } from "../components/Rich.tsx";
import { Options } from "./Options.tsx";
import type { ItemProps } from "./props.ts";

export function Fill({ item, given, onAnswer }: ItemProps<"fill">) {
  const chosen = typeof given === "number" ? given : undefined;
  const [before, after] = item.code.split(BLANK);
  const state =
    chosen === undefined ? undefined : chosen === item.right ? "ok" : "no";
  return (
    <>
      <p className="prompt">
        <Rich text={item.prompt} />
      </p>
      <pre className="code">
        <code>
          {before}
          <span className="blank" data-state={state}>
            {chosen === undefined ? BLANK : item.options[chosen]}
          </span>
          {after}
        </code>
      </pre>
      <Options
        options={item.options}
        chosen={chosen}
        right={item.right}
        mono
        onPick={onAnswer}
      />
    </>
  );
}
