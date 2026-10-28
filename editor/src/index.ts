// The editor uses CodeMirror 6 with Python and the tokens of theme.css.
// `mise run generate:scripts` bundles it into site/player/editor.js. exercise.ts loads it when the first exercise opens.
import {
  defaultKeymap,
  history,
  historyKeymap,
  indentLess,
  indentMore,
} from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import {
  HighlightStyle,
  bracketMatching,
  indentOnInput,
  indentUnit,
  syntaxHighlighting,
} from "@codemirror/language";
import { EditorState, Prec, StateEffect, StateField } from "@codemirror/state";
import {
  Decoration,
  type DecorationSet,
  EditorView,
  type KeyBinding,
  drawSelection,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
} from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

const style = HighlightStyle.define([
  {
    tag: [
      t.keyword,
      t.controlKeyword,
      t.operatorKeyword,
      t.definitionKeyword,
      t.moduleKeyword,
    ],
    color: "var(--violet)",
  },
  { tag: [t.string, t.special(t.string)], color: "var(--green)" },
  { tag: [t.number, t.bool, t.null], color: "var(--gold)" },
  { tag: t.comment, color: "var(--muted)", fontStyle: "italic" },
  {
    tag: [t.definition(t.variableName), t.function(t.variableName)],
    color: "var(--blue)",
  },
  { tag: [t.className, t.typeName, t.self, t.atom], color: "var(--teal)" },
  { tag: [t.meta, t.annotation], color: "var(--acc-text)" },
  { tag: t.invalid, color: "var(--bad)" },
]);

const theme = EditorView.theme({
  "&": {
    color: "var(--ink)",
    backgroundColor: "var(--code-bg)",
    fontSize: "16px",
    maxHeight: "min(60vh, 460px)",
    minHeight: "9.5em",
  },
  "&.cm-focused": { outline: "2px solid var(--focus)", outlineOffset: "-1px" },
  ".cm-scroller": {
    fontFamily: "var(--mono)",
    lineHeight: "1.55",
    overflow: "auto",
  },
  ".cm-content": { caretColor: "var(--acc)", padding: "10px 0" },
  ".cm-line": { padding: "0 12px 0 6px" },
  ".cm-cursor": { borderLeftColor: "var(--acc)", borderLeftWidth: "2px" },
  ".cm-gutters": {
    backgroundColor: "transparent",
    color: "var(--muted)",
    border: "none",
  },
  ".cm-lineNumbers .cm-gutterElement": {
    padding: "0 6px 0 12px",
    minWidth: "2.2em",
  },
  ".cm-activeLine": {
    backgroundColor: "color-mix(in srgb, var(--ink) 6%, transparent)",
  },
  ".cm-activeLineGutter": {
    backgroundColor: "transparent",
    color: "var(--ink)",
  },
  ".cm-selectionBackground": {
    backgroundColor: "color-mix(in srgb, var(--blue) 22%, transparent)",
  },
  "&.cm-focused .cm-selectionBackground": {
    backgroundColor: "color-mix(in srgb, var(--blue) 35%, transparent)",
  },
  ".cm-matchingBracket": {
    backgroundColor: "color-mix(in srgb, var(--acc) 25%, transparent)",
    outline: "none",
  },
  ".cm-errline": {
    backgroundColor: "color-mix(in srgb, var(--bad) 16%, transparent)",
    boxShadow: "inset 3px 0 var(--bad)",
  },
});

const markError = StateEffect.define<number>();
const errorLine = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update(deco, tr) {
    for (const e of tr.effects) {
      if (e.is(markError)) {
        const n = e.value;
        return n >= 1 && n <= tr.state.doc.lines
          ? Decoration.set([
              Decoration.line({ class: "cm-errline" }).range(
                tr.state.doc.line(n).from,
              ),
            ])
          : Decoration.none;
      }
    }
    return tr.docChanged ? Decoration.none : deco;
  },
  provide: (f) => EditorView.decorations.from(f),
});

export interface EditorOptions {
  doc: string;
  label: string;
  onChange: (doc: string) => void;
  onRun: () => void;
  onCheck: () => void;
}

export interface Editor {
  get: () => string;
  set: (text: string) => void;
  focus: () => void;
  markError: (line: number) => void;
}

function create(
  parent: HTMLElement,
  { doc, label, onChange, onRun, onCheck }: EditorOptions,
): Editor {
  // Tab indents. Esc lets the next Tab leave the editor.
  let tabOut = false;
  const tabKeys: KeyBinding[] = [
    { key: "Escape", run: () => ((tabOut = true), false) },
    {
      key: "Tab",
      run: (v) => !tabOut && indentMore(v),
      shift: (v) => !tabOut && indentLess(v),
    },
  ];
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc,
      extensions: [
        Prec.high(
          keymap.of([
            { key: "Mod-Enter", run: () => (onRun(), true) },
            { key: "Mod-Shift-Enter", run: () => (onCheck(), true) },
            ...tabKeys,
          ]),
        ),
        keymap.of([...defaultKeymap, ...historyKeymap]),
        lineNumbers(),
        highlightActiveLine(),
        highlightActiveLineGutter(),
        drawSelection(),
        history(),
        indentOnInput(),
        bracketMatching(),
        python(),
        syntaxHighlighting(style),
        indentUnit.of("    "),
        EditorState.tabSize.of(4),
        EditorView.lineWrapping,
        EditorView.contentAttributes.of({
          "aria-label": label,
          "aria-multiline": "true",
          spellcheck: "false",
          autocapitalize: "off",
          autocorrect: "off",
        }),
        EditorView.domEventHandlers({
          keydown: (e) => {
            if (e.key !== "Escape" && e.key !== "Tab") tabOut = false;
          },
          blur: () => {
            tabOut = false;
          },
        }),
        EditorView.updateListener.of((u) => {
          if (u.docChanged) onChange(u.state.doc.toString());
        }),
        errorLine,
        theme,
      ],
    }),
  });
  return {
    get: () => view.state.doc.toString(),
    set: (text) =>
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: text },
      }),
    focus: () => view.focus(),
    markError: (line) => view.dispatch({ effects: markError.of(line) }),
  };
}

declare global {
  interface Window {
    QGEditor: { create: typeof create };
  }
}

window.QGEditor = { create };
