import { ArrowLeft, Flame, Moon, Sun, Zap } from "lucide-react";
import { useEffect, useRef, useSyncExternalStore, type ReactNode } from "react";

import { useXp } from "../store.ts";

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

function Stats({ drill }: { drill?: string }) {
  const { streak, today } = useXp();
  const flame = (
    <>
      <Flame aria-hidden="true" />
      <span className="sr">Racha: </span>
      {streak}
      <span className="sr"> {streak === 1 ? "día" : "días"}</span>
    </>
  );
  return (
    <ul className="stats" aria-label="Tu racha">
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
        <Zap aria-hidden="true" />
        {today} XP<span className="sr"> hoy</span>
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
  footer?: ReactNode;
  children: ReactNode;
}

export function Layout({
  back,
  stats,
  drill,
  privacy = true,
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
          {stats ? <Stats drill={drill} /> : null}
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
