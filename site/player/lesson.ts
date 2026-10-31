// Types of lesson.json and of the contract between the engine (engine.ts) and the blocks (blocks.ts, exercise.ts).

export type Vec = [number, number];
export type Matrix = [Vec, Vec];

interface SpecBase {
  id?: string;
  hidden?: boolean;
  color?: string;
  maxw?: number;
}

export interface MathSpec extends SpecBase {
  type: "math";
  tex: string;
  size?: number;
}
export interface TextSpec extends SpecBase {
  type: "text";
  text: string;
  style?: string;
  size?: number;
}
export interface ListSpec extends SpecBase {
  type: "list";
  items: string[];
  stagger?: boolean;
  size?: number;
}
export interface RowSpec extends SpecBase {
  type: "row";
  items: Spec[];
  gap?: number;
}
export interface BoxSpec extends SpecBase {
  type: "box";
  kind?: string;
  title?: string;
  body?: Spec[];
}
export interface SpacerSpec extends SpecBase {
  type: "spacer";
  h?: number;
}

/** Size of a figure; `pw` and `ph` are the portrait size. */
export interface FigureSize {
  w: number;
  h: number;
  pw?: number;
  ph?: number;
}

/** A quantity that is a number or the name of a parameter of the plot. */
type Quantity = number | string;

export interface PlotSpec extends SpecBase, FigureSize {
  type: "plot";
  params?: Record<string, number>;
  xr: [number, number];
  yr: [number, number];
  xticks?: (number | [number, string])[];
  yticks?: (number | [number, string])[];
  yaxis?: boolean;
  xlabel?: string;
  ylabel?: string;
  curves?: {
    /** A formula in `x` and the parameters. Use `pts` for data computed in the lesson source. */
    expr?: string;
    /** A polyline of [x, y] points, drawn as given. It may loop, as an orbit does. */
    pts?: Vec[];
    hidden?: boolean;
    from?: number;
    to?: number;
    color?: string;
    width?: number;
    dash?: string;
    label?: string;
    lx?: number;
    ly?: number;
    lsize?: number;
  }[];
  areas?: {
    a: Quantity;
    b: Quantity;
    curve?: number;
    color?: string;
    opacity?: number;
    hidden?: boolean;
  }[];
  vlines?: {
    x: Quantity;
    color?: string;
    dash?: string;
    label?: string;
    ly?: number;
    hidden?: boolean;
  }[];
  points?: {
    x: Quantity;
    y?: number;
    curve?: number;
    color?: string;
    label?: string;
    dx?: number;
    dy?: number;
    hidden?: boolean;
  }[];
  labels?: {
    x: number;
    y: number;
    text: string;
    color?: string;
    size?: number;
  }[];
}

export interface PlaneVector {
  name: string;
  v: Vec;
  from?: Vec;
  color?: string;
  label?: string;
  fixed?: boolean;
  hidden?: boolean;
}
export interface PlaneSegment {
  name: string;
  a: Vec;
  b: Vec;
  color?: string;
  dash?: string;
  fixed?: boolean;
  hidden?: boolean;
}
export interface PlaneLine {
  name: string;
  dir: Vec;
  color?: string;
  fixed?: boolean;
  hidden?: boolean;
}

export interface PlaneSpec extends SpecBase, Partial<FigureSize> {
  type: "plane";
  range?: number;
  vectors?: PlaneVector[];
  segments?: PlaneSegment[];
  lines?: PlaneLine[];
  ghost?: boolean;
  grid?: boolean;
  basis?: boolean;
  basisLabels?: [string, string];
}

export interface BarsSpec extends SpecBase, FigureSize {
  type: "bars";
  data: [number, number][];
  xr?: [number, number];
  ymax?: number;
  mean: number;
  sigma: number;
  meanLabel?: string;
  xticks?: number[];
  xlabel?: string;
}

export interface DotsSpec extends SpecBase, FigureSize {
  type: "dots";
  k?: number;
  env?: number;
}

export interface CodeSpec extends SpecBase {
  type: "code";
  src: string;
  lang?: string;
  title?: string;
  numbers?: boolean;
  reveal?: boolean;
  size?: number;
  maxh?: number;
  window?: number;
}

export interface CircuitOp {
  g: string;
  q?: number[];
  ctrl?: number[];
  c?: number;
  col?: number;
  label?: string;
  p?: string;
  base?: string;
  inner?: string;
  innerColor?: string;
  color?: string;
  hidden?: boolean;
}
export interface CircuitSpec extends SpecBase {
  type: "circuit";
  qubits: number;
  ops: CircuitOp[];
  clbits?: number;
  creg?: string;
  qlabels?: string[];
  clabels?: string[];
  cidx?: boolean;
  scale?: number;
}

export type HistRow = [label: string, value: number, color?: string];
export interface HistSpec extends SpecBase {
  type: "hist";
  data: HistRow[];
  grow?: boolean;
  prob?: boolean;
  digits?: number;
  values?: boolean;
  ymax?: number;
  ymin?: number;
  ylabel?: string;
  w?: number;
  h?: number;
  ph?: number;
}

export interface TableSpec extends SpecBase {
  type: "table";
  head?: string[];
  rows: string[][];
  stagger?: boolean;
  size?: number;
}

export interface MissionSpec extends SpecBase {
  type: "mission";
  notebook: string;
  tasks: { level: number; text: string }[];
  title?: string;
  stagger?: boolean;
}

export interface FlowSpec extends SpecBase {
  type: "flow";
  steps: { t: string; s?: string; n?: number | string; color?: string }[];
  vertical?: boolean;
  stagger?: boolean;
  numbered?: boolean;
}

export interface GraphSpec extends SpecBase {
  type: "graph";
  nodes: Vec[];
  edges: Vec[];
  nodeLabels?: Record<number, string>;
  unit?: number;
  r?: number;
  numbers?: boolean;
}

export interface ExerciseSpec extends SpecBase {
  type: "exercise";
  exercise: string;
  prompt: string;
  level: number;
  starter: string;
  hints?: string[];
  cases?: string[];
  /** "fix": the starter is broken code to repair, not an empty one to complete. */
  kind?: "fix";
  /** "browser": the page grades with Pyodide, using `check`. Without it, /run grades. */
  runs?: "browser";
  /** The whole check.py of a browser-graded exercise. */
  check?: string;
}

export type Spec =
  | MathSpec
  | TextSpec
  | ListSpec
  | RowSpec
  | BoxSpec
  | SpacerSpec
  | PlotSpec
  | PlaneSpec
  | BarsSpec
  | DotsSpec
  | CodeSpec
  | CircuitSpec
  | HistSpec
  | TableSpec
  | MissionSpec
  | FlowSpec
  | GraphSpec
  | ExerciseSpec;

interface ActionBase {
  id?: string;
  /** Narration mark. */
  at?: string;
  /** Extra seconds after the mark. */
  t?: number;
  sfx?: string;
}

type ActionBody =
  | {
      do:
        | "show"
        | "hide"
        | "dim"
        | "undim"
        | "emph"
        | "unemph"
        | "sfx"
        | "unhl"
        | "clearhl"
        | "mean"
        | "sigma";
    }
  | { do: "item"; i: number }
  | { do: "tex"; tex: string }
  | { do: "text"; text: string }
  | { do: "curve"; i: number; dur?: number }
  | { do: "uncurve" | "area" | "unarea" | "vline" | "point"; i: number }
  | { do: "param"; p: string; to: number; dur?: number }
  | { do: "transform"; m: Matrix; dur?: number }
  | { do: "vec"; name: string; vec: Partial<PlaneVector> }
  | { do: "vecTo"; name: string; v: Vec; dur?: number }
  | { do: "unvec"; name: string }
  | { do: "seg"; name: string; seg: Partial<PlaneSegment> }
  | { do: "unseg"; name: string }
  | { do: "line"; name: string; line: Partial<PlaneLine> }
  | { do: "emit"; n: number; dur?: number }
  | { do: "lines"; to?: number; gap?: number }
  | { do: "hl"; lines?: number[]; range?: string; dim?: boolean }
  | { do: "gate" | "ungate" | "hlop" | "hlrow" | "step"; i?: number | number[] }
  | { do: "cursor"; col?: number }
  | { do: "grow"; dur?: number }
  | { do: "data"; data: HistRow[]; dur?: number }
  | { do: "hlnode"; i: number | number[]; color?: string }
  | { do: "hledge"; edges?: Vec[]; i?: Vec; color?: string }
  | { do: "nodelabel"; labels: Record<number, string> };

export type Action = ActionBase & ActionBody;

interface AskBase {
  label?: string;
  prompt: string;
  hint?: string;
  solution?: string | string[];
}

export type Ask =
  | (AskBase & {
      kind: "choice";
      options: string[];
      right: number;
      why?: string | string[];
      wrong?: (string | null)[];
    })
  | (AskBase & {
      kind: "numeric";
      answer: number;
      tol?: number;
      why?: string | string[];
      placeholder?: string;
      unit?: string;
    })
  | (AskBase & { kind: "reveal"; button?: string })
  | (AskBase & { kind: "predict"; options: string[]; after: string })
  | (Omit<AskBase, "prompt"> & { kind: "reflect"; prompts: string[] });

export interface Beat {
  id: string;
  title?: string;
  say: string;
  tag?: [string, string?];
  align?: string;
  hold?: number;
  scene?: Spec[];
  actions?: Action[];
  ask?: Ask;
}

export interface Lesson {
  id: string;
  part: string;
  section: string;
  title: string;
  goals?: string[];
  practice?: string[];
  next?: string | null;
  beats: Beat[];
}

/** timings.json: the duration of each clip, the second of each mark and the subtitles. */
export type Timings = Record<
  string,
  { dur: number; marks: Record<string, number>; cues: [number, string][] }
>;

/** Something with `classList.remove`: one element, or several revealed together. */
export interface Revealable {
  classList: { remove: (...tokens: string[]) => void };
}

/** What a block constructor returns. */
export interface BlockObject {
  spec: Spec;
  /** Paints again (orientation or theme change). */
  draw?: () => void;
  /** Runs an action of its own; returns true if it recognised it. */
  act?: (a: Action, instant: boolean) => boolean;
  /** Elements the generic `item` action reveals. */
  items?: Revealable[];
}

export type SvgAttrs = Record<string, string | number>;

export interface Api {
  el: <K extends keyof HTMLElementTagNameMap>(
    tag: K,
    cls?: string,
    parent?: Element,
  ) => HTMLElementTagNameMap[K];
  svg: <K extends keyof SVGElementTagNameMap>(
    tag: K,
    attrs?: SvgAttrs,
    parent?: Element,
  ) => SVGElementTagNameMap[K];
  tex: (node: HTMLElement, src: string, display?: boolean) => void;
  rich: <N extends HTMLElement>(node: N, str: string) => N;
  col: (c?: string) => string;
  cssv: (name: string) => string;
  tween: (dur: number, step: (q: number) => void, instant?: boolean) => void;
  label: (
    fig: HTMLElement,
    x: number,
    y: number,
    str: string,
    color?: string,
    size?: number,
  ) => HTMLDivElement;
  isPortrait: () => boolean;
  isReview: () => boolean;
  /** Asks to run `f` once the scene is mounted. */
  after: (f: () => void) => void;
}

export type BlockBuilder<S extends Spec> = (
  box: HTMLElement,
  s: S,
  A: Api,
) => BlockObject;
