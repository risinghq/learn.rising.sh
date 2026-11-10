import { ArrowLeft, Flame, Moon, Sun, Zap } from "lucide-react";
import { useEffect, useRef, useSyncExternalStore, type ReactNode } from "react";

import { PREF } from "@site/progress.ts";

import { useHasProgress, useStored, useXp } from "../store.ts";

const subscribeTheme = (listener: () => void) => {
  addEventListener("themechange", listener);
  return () => removeEventListener("themechange", listener);
};
const isDark = () =>
  (document.documentElement.dataset.theme ??
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) ===
  "dark";

function ThemeToggle() {
  const dark = useSyncExternalStore(subscribeTheme, isDark, () => false);
  const Icon = dark ? Sun : Moon;
  return (
    <button
      type="button"
      className="icon-btn"
      aria-label={dark ? "Tema claro" : "Tema oscuro"}
      onClick={() => toggleTheme()}
    >
      <Icon aria-hidden="true" />
    </button>
  );
}

// account.js fills this host after the page becomes interactive.
function AccountSlot() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (host.current && !host.current.hasChildNodes())
      QGAccount.mount(host.current);
  }, []);
  return <div className="acct-slot" ref={host} />;
}

function Stats({ drill, here }: { drill?: string; here?: boolean }) {
  const account = useStored(PREF.account);
  const { streak, today } = useXp();
  const earned = useHasProgress();
  const signedIn = account !== null;
  if (!signedIn && !earned) return <ul className="stats" aria-hidden="true" />;
  const flame = (
    <>
      <Flame aria-hidden="true" />
      <span className="sr">Racha: </span>
      {streak}
      <span className="sr"> {streak === 1 ? "día" : "días"}</span>
    </>
  );
  return (
    <ul className="stats" aria-label="Tu progreso y tus amigos">
      <li className="stat" data-active={streak > 0}>
        {drill ? (
          <a href={`/${drill}/repaso/`}>
            {flame}
            <span className="sr">. Empezar un repaso</span>
          </a>
        ) : (
          flame
        )}
      </li>
      <li className="stat">
        {signedIn ? (
          <a
            href="/amigos/"
            aria-label={`${today} XP hoy. Ver amigos y tablero`}
            aria-current={here ? "page" : undefined}
          >
            <Zap aria-hidden="true" />
            {today} XP<span className="sr"> hoy</span>
          </a>
        ) : (
          <>
            <Zap aria-hidden="true" />
            {today} XP<span className="sr"> hoy</span>
          </>
        )}
      </li>
    </ul>
  );
}

interface LayoutProps {
  back?: boolean;
  stats?: boolean;
  /** The course whose review session the streak opens. */
  drill?: string;
  privacy?: boolean;
  /** Marks the friends page as current in the XP link. */
  here?: boolean;
  footer?: ReactNode;
  children: ReactNode;
}

export function Layout({
  back,
  stats,
  drill,
  privacy = true,
  here,
  footer,
  children,
}: LayoutProps) {
  return (
    <>
      <a className="skip" href="#main">
        Saltar al contenido
      </a>
      <header className="top">
        <div className="in">
          <div>
            {back ? (
              <a className="icon-btn" href="/" aria-label="Todos los cursos">
                <ArrowLeft aria-hidden="true" />
              </a>
            ) : (
              <a className="brand" href="/">
                Rising
              </a>
            )}
          </div>
          <span className="sp" />
          {stats ? <Stats drill={drill} here={here} /> : null}
          <AccountSlot />
          <ThemeToggle />
        </div>
      </header>
      <main id="main">{children}</main>
      <footer className="foot">
        {footer ? <p>{footer}</p> : null}
        {privacy ? (
          <p>
            <a href="/privacidad.html">Privacidad</a>
          </p>
        ) : null}
      </footer>
    </>
  );
}
