// The learner's progress as React state. localStorage is the source, so the server render and the
// first client render see nothing stored and the pages then repaint with what the browser holds.
import { useEffect, useMemo, useState, useSyncExternalStore } from "react";

import {
  ACCOUNT_EVENT,
  addXp,
  courseKey,
  PREF,
  read,
  standing,
  xpQueueKey,
  write,
} from "@site/progress.ts";

const listeners = new Set<() => void>();

/** Tells every component that something stored changed. */
export const notify = () => {
  for (const listener of listeners) listener();
};

function subscribe(listener: () => void) {
  listeners.add(listener);
  addEventListener("storage", listener);
  addEventListener(ACCOUNT_EVENT, listener);
  return () => {
    listeners.delete(listener);
    removeEventListener("storage", listener);
    removeEventListener(ACCOUNT_EVENT, listener);
  };
}

const nothing = () => null;

export const useStored = (key: string): string | null =>
  useSyncExternalStore(subscribe, () => read(key), nothing);

function parse<T>(raw: string | null, fallback: T): T {
  try {
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

/** The XP the signed-in account has not sent, as stored. It changes when the queue or the account does. */
export const useOutbox = (): string | null =>
  useStored(xpQueueKey(useStored(PREF.account)));

/** The JSON stored under `key`. The fallback must be a constant, so the value only changes with the storage. */
export function useJson<T>(key: string, fallback: T): T {
  const raw = useStored(key);
  return useMemo(() => parse(raw, fallback), [raw, fallback]);
}

/** Stores a value and tells the account, which sends it if the learner has one. */
export function save(key: string, value: unknown) {
  write(key, JSON.stringify(value));
  QGAccount.changed(key);
  notify();
}

/** Adds to today's XP, which stays in this browser, and repaints the streak. */
export function awardXp(amount: number) {
  addXp(amount);
  notify();
}

const NO_IDS: string[] = [];

export function useDone(course: string): ReadonlySet<string> {
  const ids = useJson(courseKey(course, "done"), NO_IDS);
  return useMemo(() => new Set(Array.isArray(ids) ? ids : NO_IDS), [ids]);
}

export const useLastCourse = () => useStored(PREF.last);

const NO_XP = { today: 0, streak: 0 };

/** Shows the account's totals when signed in and the browser's totals otherwise. */
export function useXp() {
  const key = useSyncExternalStore(
    subscribe,
    () =>
      JSON.stringify([
        read(PREF.xp),
        read(PREF.account),
        read(PREF.tally),
        read(xpQueueKey(read(PREF.account))),
      ]),
    nothing,
  );
  // The server render and the first client render have no key. Show no totals then.
  return useMemo(() => (key === null ? NO_XP : standing()), [key]);
}

/** The lessons done in each of several courses, from one subscription. */
export function useDoneByCourse(
  slugs: string[],
): Record<string, ReadonlySet<string>> {
  const raw = useSyncExternalStore(
    subscribe,
    () => JSON.stringify(slugs.map((slug) => read(courseKey(slug, "done")))),
    nothing,
  );
  return useMemo(() => {
    const stored = raw === null ? [] : (JSON.parse(raw) as (string | null)[]);
    return Object.fromEntries(
      slugs.map((slug, k) => {
        const ids = parse<unknown>(stored[k] ?? null, NO_IDS);
        return [slug, new Set(Array.isArray(ids) ? (ids as string[]) : NO_IDS)];
      }),
    );
  }, [raw, slugs]);
}

/** True once the account has merged its progress, so the page can read what the browser holds. */
export function useReady() {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    let live = true;
    void QGAccount.ready.then(() => {
      if (!live) return;
      setReady(true);
      notify();
    });
    return () => {
      live = false;
    };
  }, []);
  return ready;
}
