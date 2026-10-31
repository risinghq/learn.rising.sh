import { Bell, BellOff } from "lucide-react";
import { useEffect, useState } from "react";

import { current, disable, enable, settings, type Reminders } from "../push.ts";

const WRONG = "No se pudo cambiar el aviso. Inténtalo de nuevo.";

/**
 * The opt-in for the streak reminder. `quiet` leaves the control out where the browser cannot
 * receive it, so the end of a session offers nothing it cannot deliver.
 */
export function Reminder({ quiet = false }: { quiet?: boolean }) {
  const [state, setState] = useState<Reminders>();
  const [hour, setHour] = useState<number>();
  const [unavailable, setUnavailable] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let live = true;
    current().then(
      async (now) => {
        // The hour belongs to the account's schedule, so a browser that is
        // already subscribed asks for it.
        if (now === "on") setHour((await settings().catch(() => null))?.hour);
        if (live) setState(now);
      },
      () => live && setState("unsupported"),
    );
    return () => {
      live = false;
    };
  }, []);

  if (state === undefined) return null;
  if (state === "unsupported")
    return quiet ? null : (
      <p className="muted">
        Este navegador no admite avisos. En iPhone, añade Rising a la pantalla
        de inicio para activarlos.
      </p>
    );
  if (state === "blocked")
    return quiet ? null : (
      <p className="muted">
        Bloqueaste los avisos de este sitio. Permítelos en los ajustes del
        navegador para activar el recordatorio.
      </p>
    );

  const toggle = async () => {
    setBusy(true);
    setMessage("");
    try {
      if (state === "on") {
        await disable();
        setState("off");
        return;
      }
      const found = await settings();
      if (!found) {
        setUnavailable(true);
        return;
      }
      setHour(found.hour);
      setState(await enable(found.key));
    } catch {
      setMessage(WRONG);
    } finally {
      setBusy(false);
    }
  };

  if (unavailable)
    return quiet ? null : (
      <p className="muted">Los avisos no están disponibles ahora.</p>
    );
  const Icon = state === "on" ? BellOff : Bell;
  return (
    <div className="reminder">
      <button
        type="button"
        className="btn"
        aria-busy={busy}
        onClick={() => void toggle()}
      >
        <Icon aria-hidden="true" />
        {state === "on"
          ? "Quitar el aviso de racha"
          : "Avisarme si olvido mi racha"}
      </button>
      <p className="muted" role="status">
        {message ||
          (state === "on" && hour !== undefined
            ? `Te avisamos a las ${hour}:00 si ese día aún no practicaste.`
            : "")}
      </p>
    </div>
  );
}
