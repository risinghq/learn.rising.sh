import { Rich } from "../components/Rich.tsx";
import { Options } from "./Options.tsx";
import type { ItemProps } from "./props.ts";

export function Predict({ item, given, onAnswer }: ItemProps<"predict">) {
  return (
    <>
      <p className="prompt">
        <Rich text={item.prompt} />
      </p>
      <Options
        options={item.options}
        chosen={typeof given === "number" ? given : undefined}
        onPick={onAnswer}
      />
    </>
  );
}
