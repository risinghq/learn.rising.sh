import { Rich } from "../components/Rich.tsx";
import { Options } from "./Options.tsx";
import type { ItemProps } from "./props.ts";

export function Choice({ item, given, onAnswer }: ItemProps<"choice">) {
  return (
    <>
      <p className="prompt">
        <Rich text={item.prompt} />
      </p>
      <Options
        options={item.options}
        chosen={typeof given === "number" ? given : undefined}
        right={item.right}
        onPick={onAnswer}
      />
    </>
  );
}
