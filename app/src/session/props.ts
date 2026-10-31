import type { Answer } from "../../../drill/grade.ts";
import type { ItemKind, ItemOf } from "../../../drill/item.ts";

export interface ItemProps<K extends ItemKind> {
  item: ItemOf<K>;
  given: Answer | undefined;
  onAnswer: (answer: Answer) => void;
  seed: string;
}
