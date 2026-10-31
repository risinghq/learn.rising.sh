import { X } from "lucide-react";
import type { ReactNode } from "react";

export function Frame({
  slug,
  progress,
  children,
}: {
  slug: string;
  progress?: { value: number; max: number };
  children: ReactNode;
}) {
  return (
    <div className="drill">
      <header className="drill-top">
        <a
          className="icon-btn"
          href={`/${slug}/`}
          aria-label="Volver al camino"
        >
          <X aria-hidden="true" />
        </a>
        {progress ? (
          <progress
            max={progress.max}
            value={progress.value}
            aria-label="Progreso del repaso"
          />
        ) : null}
      </header>
      <main id="main" className="drill-main">
        {children}
      </main>
    </div>
  );
}
