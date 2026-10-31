import { Check, Copy, Flame, Share2, UserPlus } from "lucide-react";
import { PREF } from "@site/progress.ts";
import { useEffect, useRef, useState } from "react";

import { refusal, useCircle, weekEnd, type Circle } from "../friends.ts";
import { useOutbox, useReady, useStored, useXp } from "../store.ts";
import { Layout } from "./Layout.tsx";
import { Reminder } from "./Reminder.tsx";

const DAY = new Intl.DateTimeFormat("es", {
  weekday: "long",
  day: "numeric",
  month: "long",
});
const pad = (n: number) => String(n).padStart(2, "0");

const inviteCode = () => new URLSearchParams(location.search).get("c");

const days = (n: number) => `${n} ${n === 1 ? "día" : "días"}`;

function SignIn({ children }: { children: string }) {
  return (
    <section className="card" aria-labelledby="t-enter">
      <h2 id="t-enter">{children}</h2>
      <div className="actions">
        <a className="btn primary" href={QGAccount.signInHref("google")}>
          Entrar con Google
        </a>
        <a className="btn" href={QGAccount.signInHref("github")}>
          Entrar con GitHub
        </a>
      </div>
    </section>
  );
}

/** The week's end, with the time left ticking as a clock. */
function WeekEnd({ weekStart }: { weekStart: string }) {
  const end = weekEnd(weekStart);
  const [now, setNow] = useState<number>();
  useEffect(() => {
    setNow(Date.now());
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(tick);
  }, []);
  const last = new Date(end.getTime() - 1);
  const left = Math.max(0, end.getTime() - (now ?? end.getTime()));
  const d = Math.floor(left / 86_400_000);
  const h = Math.floor(left / 3_600_000) % 24;
  const m = Math.floor(left / 60_000) % 60;
  const s = Math.floor(left / 1000) % 60;
  return (
    <p className="muted">
      Termina el <time dateTime={weekStart}>{DAY.format(last)}</time>
      {now === undefined ? null : (
        <>
          . Quedan{" "}
          <span className="num" aria-hidden="true">
            {d} d {pad(h)}:{pad(m)}:{pad(s)}
          </span>
        </>
      )}
    </p>
  );
}

function Board({
  circle,
  nameOf,
}: {
  circle: Circle;
  nameOf: (id: number) => string;
}) {
  return (
    <table className="board">
      <caption className="sr">Tablero de la semana</caption>
      <thead>
        <tr>
          <th scope="col">Puesto</th>
          <th scope="col">Quién</th>
          <th scope="col" className="amount">
            XP
          </th>
        </tr>
      </thead>
      <tbody>
        {circle.entries.map((entry) => (
          <tr key={entry.id ?? "you"} data-you={entry.you}>
            <td className="num">{entry.rank}</td>
            <th scope="row">{entry.you ? "Tú" : nameOf(entry.id!)}</th>
            <td className="num amount">{entry.xp}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Invite({ solo }: { solo: boolean }) {
  const [link, setLink] = useState<{ url: string; expires: number }>();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const field = useRef<HTMLInputElement>(null);
  const canShare = typeof navigator.share === "function";

  const create = async () => {
    setBusy(true);
    setNote("");
    try {
      const resp = await QGAccount.request("POST", "/api/friends/invite");
      if (!resp.ok) return setNote(await refusal(resp));
      const body = (await resp.json()) as { code: string; expiresAt: number };
      setLink({
        url: `${location.origin}/amigos/?c=${body.code}`,
        expires: body.expiresAt,
      });
    } catch {
      setNote("No se pudo crear el enlace. Inténtalo de nuevo.");
    } finally {
      setBusy(false);
    }
  };

  // Sharing runs straight from the tap: browsers drop the share sheet after an await.
  const share = () => {
    if (!link) return;
    navigator
      .share({
        title: "Rising",
        text: "Practica conmigo en Rising. Acepta mi invitación:",
        url: link.url,
      })
      .then(
        () => setNote("Invitación compartida."),
        (error: unknown) => {
          if ((error as Error).name !== "AbortError")
            setNote("No se pudo compartir. Copia el enlace.");
        },
      );
  };
  const copy = () => {
    if (!link) return;
    navigator.clipboard.writeText(link.url).then(
      () => setNote("Enlace copiado."),
      () => {
        field.current?.select();
        setNote("Selecciona el enlace y cópialo.");
      },
    );
  };

  if (!link)
    return (
      <div className="invite">
        <button
          type="button"
          className={solo ? "btn primary" : "btn"}
          aria-busy={busy}
          onClick={() => void create()}
        >
          <UserPlus aria-hidden="true" />
          Invitar a un amigo
        </button>
        <p className="muted" role="status">
          {note}
        </p>
      </div>
    );
  return (
    <div className="invite">
      <div className="field">
        <label htmlFor="invite-link">Enlace de invitación</label>
        <p id="invite-hint" className="muted">
          Sirve para una persona y vence el {DAY.format(new Date(link.expires))}
          .
        </p>
        <input
          id="invite-link"
          ref={field}
          readOnly
          value={link.url}
          aria-describedby="invite-hint"
          onFocus={(event) => event.currentTarget.select()}
        />
      </div>
      <div className="actions">
        {canShare ? (
          <button type="button" className="btn primary" onClick={share}>
            <Share2 aria-hidden="true" />
            Compartir enlace
          </button>
        ) : null}
        <button
          type="button"
          className={canShare ? "btn" : "btn primary"}
          onClick={copy}
        >
          <Copy aria-hidden="true" />
          Copiar enlace
        </button>
      </div>
      <p className="muted" role="status">
        {note}
      </p>
    </div>
  );
}

function Friends({
  circle,
  nameOf,
  reload,
}: {
  circle: Circle;
  nameOf: (id: number) => string;
  reload: () => Promise<void>;
}) {
  const [asking, setAsking] = useState<number>();
  const [note, setNote] = useState("");

  const remove = async (id: number) => {
    const resp = await QGAccount.request("DELETE", `/api/friends/${id}`);
    setAsking(undefined);
    if (!resp.ok) return setNote(await refusal(resp));
    setNote(`${nameOf(id)} ya no está en tu tablero.`);
    await reload();
  };

  return (
    <>
      <ul className="friends">
        {circle.friends.map((friend) => (
          <li key={friend.id}>
            <div className="who">
              <span className="title">{nameOf(friend.id)}</span>
              <span className="meta num">
                <span>
                  <Flame aria-hidden="true" data-active={friend.streak > 0} />
                  {days(friend.streak)}
                  <span className="sr"> de racha</span>
                </span>
                <span>
                  {friend.today ? <Check aria-hidden="true" /> : null}
                  {friend.today ? "Practicó hoy" : "Aún no practica hoy"}
                </span>
              </span>
            </div>
            {asking === friend.id ? (
              <div
                className="confirm"
                role="group"
                aria-label={`Quitar a ${nameOf(friend.id)}`}
              >
                <p className="muted">Dejan de verse en el tablero.</p>
                <button
                  type="button"
                  className="btn danger"
                  onClick={() => void remove(friend.id)}
                >
                  Quitar amigo
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={() => setAsking(undefined)}
                >
                  Conservar
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn"
                aria-label={`Quitar a ${nameOf(friend.id)}`}
                onClick={() => setAsking(friend.id)}
              >
                Quitar
              </button>
            )}
          </li>
        ))}
      </ul>
      <p className="muted" role="status">
        {note}
      </p>
    </>
  );
}

/** Accepts the invitation of the address, once the learner has an account. */
function Accept({
  code,
  signedIn,
  done,
}: {
  code: string;
  signedIn: boolean;
  done: (note: string) => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  if (!signedIn)
    return <SignIn>Te invitaron a Rising. Entra para aceptar</SignIn>;
  const accept = async () => {
    setBusy(true);
    setError("");
    try {
      const resp = await QGAccount.request("POST", "/api/friends/accept", {
        code,
      });
      if (!resp.ok) return setError(await refusal(resp));
      history.replaceState(null, "", "/amigos/");
      done("Ahora son amigos.");
    } catch {
      setError("No se pudo aceptar. Inténtalo de nuevo.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="card" aria-labelledby="t-accept">
      <h2 id="t-accept">Te invitaron a Rising</h2>
      <p className="muted">
        Si aceptas, se ven en el tablero de la semana y en la lista de amigos.
      </p>
      <button
        type="button"
        className="btn primary"
        aria-busy={busy}
        onClick={() => void accept()}
      >
        Aceptar invitación
      </button>
      <p className="muted" role="alert">
        {error}
      </p>
    </section>
  );
}

export function FriendsPage() {
  const ready = useReady();
  const signedIn = useStored(PREF.account) !== null;
  const { streak } = useXp();
  const outbox = useOutbox();
  const { circle, failed, reload, nameOf } = useCircle(
    ready && signedIn,
    outbox,
  );
  const [code, setCode] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  useEffect(() => setCode(inviteCode()), []);

  const accepted = (note: string) => {
    setCode(null);
    setNotice(note);
    void reload();
  };
  const none = circle?.friends.length === 0;
  const mine = circle?.entries.find((entry) => entry.you)?.xp ?? 0;

  return (
    <Layout stats back here footer={<a href="/">Volver al inicio</a>}>
      <div className="page friends-page">
        <h1>Amigos</h1>
        <p className="notice" role="status">
          {notice}
        </p>
        {ready && code ? (
          <Accept code={code} signedIn={signedIn} done={accepted} />
        ) : null}
        {ready && !signedIn && !code ? (
          <SignIn>Entra para ver a tus amigos</SignIn>
        ) : null}
        {ready && signedIn ? (
          <>
            <section aria-labelledby="t-streak" className="streak-card">
              <h2 id="t-streak">Tu racha</h2>
              <p className="streak num">
                <Flame aria-hidden="true" data-active={streak > 0} />
                {days(streak)}
              </p>
              <Reminder />
            </section>
            {failed && !circle ? (
              <p role="alert">
                No se pudo cargar tu tablero. Recarga la página.
              </p>
            ) : null}
            {circle ? (
              <section aria-labelledby="t-week">
                <h2 id="t-week">Esta semana</h2>
                <WeekEnd weekStart={circle.weekStart} />
                {none ? (
                  <div className="empty">
                    <p>
                      Llevas <span className="num">{mine}</span> XP esta semana.
                      Invita a un amigo y veremos quién va primero.
                    </p>
                    <Invite solo={!code} />
                  </div>
                ) : (
                  <Board circle={circle} nameOf={nameOf} />
                )}
              </section>
            ) : null}
            {circle && !none ? (
              <section aria-labelledby="t-friends">
                <h2 id="t-friends">Tus amigos</h2>
                <Friends circle={circle} nameOf={nameOf} reload={reload} />
                <Invite solo={false} />
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </Layout>
  );
}
