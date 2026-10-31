// What the page scripts share through `window`.

/** account.ts: the optional account. */
declare var QGAccount: {
  /** Resolves once the account's progress has been merged with the local one. */
  ready: Promise<void>;
  /** Signals that the value stored under `key` changed. */
  changed: (key: string) => void;
  /** Fills `host` with the account button and its menu, for pages that render their own markup. */
  mount: (host: HTMLElement) => void;
  /** Sends an award to the account, now or when the connection returns. `ref` is unique per source and day. */
  xp: (
    source: "drill" | "lesson" | "exercise" | "browser",
    ref: string,
    amount: number,
  ) => void;
  /** Calls the account's API. A 401 closes the sign-in before the response comes back. */
  request: (method: string, path: string, body?: unknown) => Promise<Response>;
  /** The address that starts the sign-in with `provider` and returns to this page. */
  signInHref: (provider: "google" | "github") => string;
  /** Whether this browser holds a session of the account. */
  signedIn: () => boolean;
  /** Closes the sign-in if `resp` is a 401, and says whether it was. */
  lapsed: (resp: Response) => boolean;
};
/** engine.ts: the narration audio, for the automated tests. */
declare var QGNarration: HTMLAudioElement;
/** notebooks.ts: appends the "how to run the notebooks" line to `parent`. */
declare var notebookHelp: (parent: Element) => HTMLParagraphElement;
/** theme.ts: switches between the light and the dark theme. */
declare var toggleTheme: () => void;

/** The Python sources that pyodide-grader.ts bundles as text. */
declare module "*.py" {
  const text: string;
  export default text;
}
