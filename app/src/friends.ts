import { PREF, readJson, write } from "@site/progress.ts";
import { useCallback, useEffect, useRef, useState } from "react";

export interface Friend {
  id: number;
  streak: number;
  today: boolean;
  xp: number;
}

export interface Entry {
  rank: number;
  you: boolean;
  id: number | null;
  xp: number;
}

export interface Circle {
  friends: Friend[];
  /** Monday of the week the board counts, as `YYYY-MM-DD`. */
  weekStart: string;
  entries: Entry[];
}

/** The message of a refused request: the account words it for the learner. */
export async function refusal(resp: Response): Promise<string> {
  try {
    const body = (await resp.json()) as { error?: string };
    if (body.error) return body.error;
  } catch {}
  return resp.status === 429
    ? "Demasiados intentos. Espera un momento."
    : "No se pudo completar. Inténtalo de nuevo.";
}

/** The moment the board's week ends: midnight after its Sunday, in this browser's zone. */
export function weekEnd(weekStart: string): Date {
  const [year, month, day] = weekStart.split("-").map(Number);
  return new Date(year, month - 1, day + 7);
}

/**
 * Friends carry no name: the account stores none. Each gets a number, in the order this browser
 * first saw them, and keeps it.
 */
function ordinals(ids: number[]): Record<number, number> {
  const known = readJson<Record<number, number>>(PREF.friends, {});
  let next = Math.max(0, ...Object.values(known)) + 1;
  let grew = false;
  for (const id of ids)
    if (known[id] === undefined) {
      known[id] = next++;
      grew = true;
    }
  if (grew) write(PREF.friends, JSON.stringify(known));
  return known;
}

/**
 * Loads the friends and the board of a learner with an account, and again on `reload`. The board
 * also loads again when `outbox`, the XP not yet sent, changes, so it counts what has just landed.
 */
export function useCircle(signedIn: boolean, outbox: string | null) {
  const [circle, setCircle] = useState<Circle>();
  const [names, setNames] = useState<Record<number, number>>({});
  const [failed, setFailed] = useState(false);
  // Loads overlap when the outbox changes while one runs. Only the latest may set the state: an
  // earlier one can have read the friends and the board on either side of a change.
  const latest = useRef(0);

  const reload = useCallback(async () => {
    const mine = ++latest.current;
    try {
      const [friends, board] = await Promise.all([
        QGAccount.request("GET", "/api/friends"),
        QGAccount.request("GET", "/api/board"),
      ]);
      if (!friends.ok || !board.ok) throw new Error("account");
      const list = ((await friends.json()) as { friends: Friend[] }).friends;
      const week = (await board.json()) as Pick<
        Circle,
        "weekStart" | "entries"
      >;
      if (mine !== latest.current) return;
      setNames(ordinals(list.map((friend) => friend.id)));
      setCircle({ friends: list, ...week });
      setFailed(false);
    } catch {
      if (mine === latest.current) setFailed(true);
    }
  }, []);

  useEffect(() => {
    if (signedIn) void reload();
    else setCircle(undefined);
  }, [signedIn, reload, outbox]);

  return {
    circle,
    failed,
    reload,
    nameOf: (id: number) => `Amigo ${names[id] ?? id}`,
  };
}
