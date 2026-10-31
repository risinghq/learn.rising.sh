import { useEffect, useState, type ComponentType } from "react";

import type { SessionPage as Page } from "../model.ts";
import { Frame } from "../session/Frame.tsx";

// The session, the scheduler and the graders load in a chunk of their own: no other page needs
// them. The prerendered page and the first client render show the same frame, so it hydrates.
export function SessionPage({ page }: { page: Page }) {
  const { slug } = page.course;
  const [Session, setSession] = useState<ComponentType<{ slug: string }>>();
  useEffect(() => {
    void import("../session/Session.tsx").then((module) =>
      setSession(() => module.default),
    );
  }, []);
  if (Session) return <Session slug={slug} />;
  return (
    <Frame slug={slug}>
      <div className="stage">
        <p className="muted">Cargando…</p>
      </div>
    </Frame>
  );
}
