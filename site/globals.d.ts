// What the page scripts share through `window`.

/** account.ts: the optional account. */
declare var QGAccount: {
  /** Resolves once the account's progress has been merged with the local one. */
  ready: Promise<void>;
  /** Signals that the value stored under `key` changed. */
  changed: (key: string) => void;
};
/** engine.ts: the narration audio, for the automated tests. */
declare var QGNarration: HTMLAudioElement;
/** notebooks.ts: appends the "how to run the notebooks" line to `parent`. */
declare var notebookHelp: (parent: Element) => HTMLParagraphElement;
/** theme.ts: switches between the light and the dark theme. */
declare var toggleTheme: () => void;
