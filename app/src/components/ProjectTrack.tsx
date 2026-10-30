import { Check } from "lucide-react";
import { useMemo } from "react";

import { courseKey } from "@site/progress.ts";

import type { Part, Project } from "../model.ts";
import { splitTitle } from "../path.ts";
import { save, useJson } from "../store.ts";
import { Command, NotebookHelp } from "./Command.tsx";

const NO_MILESTONES: number[] = [];

export function ProjectTrack({
  slug,
  project,
  parts,
}: {
  slug: string;
  project: Project;
  parts: Part[];
}) {
  const key = courseKey(slug, "hitos");
  const done = useJson(key, NO_MILESTONES);
  const { milestones } = project;
  const linked = useMemo(
    () =>
      new Set(
        parts
          .flatMap((p) => p.lessons)
          .flatMap((l) => l.missions ?? [])
          .map((m) => m.notebook),
      ),
    [parts],
  );
  const current = milestones.find((m) => !done.includes(m.n));
  const open = current !== undefined && linked.has(current.notebook);

  return (
    <section className="project" aria-labelledby="t-proyecto">
      <h2 id="t-proyecto">{project.title}</h2>
      <p className="muted">{project.tagline}</p>
      <ol className="track" aria-label="Hitos del proyecto">
        {milestones.map((m) => {
          const finished = done.includes(m.n);
          return (
            <li
              key={m.n}
              className="hito"
              data-state={
                finished
                  ? "done"
                  : m === current
                    ? "current"
                    : linked.has(m.notebook)
                      ? "open"
                      : "locked"
              }
              aria-current={m === current ? "step" : undefined}
              title={`Hito ${m.n}: ${m.title}`}
            >
              {finished ? <Check aria-hidden="true" /> : m.n}
              {finished ? <span className="sr"> (hecho)</span> : null}
            </li>
          );
        })}
      </ol>
      {current ? (
        <div className="hcur">
          <p className="muted num">
            Hito {current.n} de {milestones.length}, parte {current.part}
          </p>
          <h3>{current.title}</h3>
          <p>{current.desc}</p>
          {open ? (
            <>
              <Command command={`uv run marimo edit ${current.notebook}`} />
              <button
                type="button"
                className="btn"
                onClick={() => save(key, [...new Set([...done, current.n])])}
              >
                Marcar como hecho
              </button>
              <NotebookHelp />
            </>
          ) : (
            <p className="muted">
              Se abre cuando llegues a la parte {current.part} (
              {splitTitle(parts[current.part - 1].title).name}).
            </p>
          )}
        </div>
      ) : (
        <p>Terminaste los {milestones.length} hitos.</p>
      )}
    </section>
  );
}
