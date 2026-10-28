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
/** course-home.ts: the list of parts of a course home page. */
declare var QGHome: {
  /** Appends a card per part of `course.json` to `root`. */
  renderParts: (
    root: HTMLElement,
    parts: {
      title: string;
      desc: string;
      lessons: {
        id: string;
        section: string;
        title: string;
        minutes?: number;
        missions?: unknown;
      }[];
    }[],
    done: Set<string>,
  ) => void;
  /** The minutes of narration of the lessons. */
  minutesOf: (lessons: { minutes?: number }[]) => number;
};
