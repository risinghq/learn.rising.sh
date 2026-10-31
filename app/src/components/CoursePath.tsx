import {
  ArrowRight,
  Check,
  ChevronDown,
  Dumbbell,
  Lock,
  Play,
} from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";

import { courseKey } from "@site/progress.ts";

import type { CoursePage, Lesson, Part } from "../model.ts";
import {
  lessonHref,
  lessonsOf,
  nextLesson,
  notebookCommand,
  pendingMission,
  splitTitle,
  stateOf,
} from "../path.ts";
import { save, useDone, useJson, useReady } from "../store.ts";
import { Command, NotebookHelp } from "./Command.tsx";
import { Layout } from "./Layout.tsx";
import { ProjectTrack } from "./ProjectTrack.tsx";

const NO_NOTEBOOKS: string[] = [];

const label = (lesson: Lesson) => `${lesson.section} ${lesson.title}`;

function Practice({
  slug,
  lessons,
  done,
}: {
  slug: string;
  lessons: Lesson[];
  done: ReadonlySet<string>;
}) {
  const key = courseKey(slug, "misiones");
  const marked = useJson(key, NO_NOTEBOOKS);
  const pending = pendingMission(lessons, done, marked);
  if (!pending) return null;
  const { lesson, mission } = pending;
  return (
    <section className="card practice" aria-labelledby="t-practica">
      <h2 id="t-practica">Práctica pendiente</h2>
      <p>
        <b>{label(lesson)}</b>
      </p>
      <p className="muted">
        {mission.tasks === 1 ? "1 misión" : `${mission.tasks} misiones`} en el
        cuaderno. Busca {mission.tasks === 1 ? "la ✅" : "las ✅"}.
      </p>
      <Command command={notebookCommand(mission.notebook)} />
      <button
        type="button"
        className="btn"
        onClick={() => save(key, [...marked, mission.notebook])}
      >
        Ya la hice
      </button>
      <NotebookHelp />
    </section>
  );
}

function ReviewCard({ slug }: { slug: string }) {
  return (
    <section className="card review" aria-labelledby="t-repaso">
      <h2 id="t-repaso">Repaso de hoy</h2>
      <p className="muted num">3 min</p>
      <a className="btn" href={`/${slug}/repaso/`}>
        <Dumbbell aria-hidden="true" />
        Repasar
      </a>
    </section>
  );
}

function LockedNode({
  slug,
  lesson,
  next,
}: {
  slug: string;
  lesson: Lesson;
  next: Lesson | undefined;
}) {
  const [open, setOpen] = useState(false);
  const note = useId();
  return (
    <li>
      <button
        type="button"
        className="node"
        data-state="locked"
        aria-expanded={open}
        aria-controls={note}
        onClick={() => setOpen(!open)}
      >
        <span className="dot">
          <Lock aria-hidden="true" />
        </span>
        <span className="text">
          <span className="title">{label(lesson)}</span>
          <span className="meta num">{lesson.minutes} min</span>
        </span>
      </button>
      <p className="unlock" id={note} hidden={!open}>
        {next ? `Termina «${next.title}» antes. ` : ""}
        <a href={lessonHref(slug, lesson.id)}>Abrir de todos modos</a>
      </p>
    </li>
  );
}

function Node({
  slug,
  lesson,
  next,
  done,
}: {
  slug: string;
  lesson: Lesson;
  next: Lesson | undefined;
  done: ReadonlySet<string>;
}) {
  const state = stateOf(lesson, next, done);
  if (state === "locked")
    return <LockedNode slug={slug} lesson={lesson} next={next} />;
  const current = state === "current";
  const Icon = current ? Play : Check;
  return (
    <li>
      <a
        className="node"
        data-state={state}
        data-current={current || undefined}
        aria-current={current ? "step" : undefined}
        href={lessonHref(slug, lesson.id)}
      >
        <span className="dot">
          <Icon aria-hidden="true" />
        </span>
        <span className="text">
          <span className="title">{label(lesson)}</span>
          {current ? (
            <>
              <span className="summary">{lesson.summary}</span>
              <span className="go num">
                {done.size ? "Continuar" : "Empezar"} · {lesson.minutes} min
                <ArrowRight aria-hidden="true" />
              </span>
            </>
          ) : (
            <span className="meta">Hecha</span>
          )}
        </span>
      </a>
    </li>
  );
}

function Unit({
  slug,
  part,
  index,
  next,
  done,
}: {
  slug: string;
  part: Part;
  index: number;
  next: Lesson | undefined;
  done: ReadonlySet<string>;
}) {
  const { label: unitLabel, name } = splitTitle(part.title);
  const finished = part.lessons.filter((l) => done.has(l.id)).length;
  const status =
    finished === part.lessons.length
      ? "done"
      : part.lessons.includes(next as Lesson)
        ? "current"
        : "locked";
  return (
    <details className="unit" data-state={status} open={status === "current"}>
      <summary>
        <span className="badge" data-state={status}>
          {status === "done" ? (
            <Check aria-hidden="true" />
          ) : status === "locked" ? (
            <Lock aria-hidden="true" />
          ) : (
            index + 1
          )}
        </span>
        <h2>
          <small>{unitLabel}</small>
          {name}
        </h2>
        <span className="num count">
          {finished}/{part.lessons.length}
        </span>
        <ChevronDown className="chev" aria-hidden="true" />
      </summary>
      <p className="muted">{part.desc}</p>
      <ol className="nodes">
        {part.lessons.map((lesson) => (
          <Node
            key={lesson.id}
            slug={slug}
            lesson={lesson}
            next={next}
            done={done}
          />
        ))}
      </ol>
    </details>
  );
}

export function CoursePath({ page }: { page: CoursePage }) {
  const { course, parts, project } = page;
  const lessons = lessonsOf(parts);
  const done = useDone(course.slug);
  const next = nextLesson(lessons, done);
  const finished = lessons.filter((l) => done.has(l.id)).length;
  const ready = useReady();
  const root = useRef<HTMLDivElement>(null);
  const scrolled = useRef(false);

  useEffect(() => {
    if (!ready || scrolled.current) return;
    scrolled.current = true;
    const node = root.current?.querySelector("[data-current]");
    if (node && node.getBoundingClientRect().bottom > innerHeight)
      node.scrollIntoView({ block: "center" });
  }, [ready]);

  const footer = (
    <>
      {course.source ? (
        <>
          Contenido basado en las{" "}
          <a href={course.source.url}>{course.source.label}</a> (
          {course.source.license}).{" "}
        </>
      ) : null}
      {course.note}
    </>
  );

  return (
    <Layout
      back
      stats
      drill={finished > 0 ? course.slug : undefined}
      footer={course.source || course.note ? footer : undefined}
    >
      <div className="page" ref={root}>
        <h1>{course.title}</h1>
        <div className="meter">
          <progress
            max={lessons.length}
            value={finished}
            aria-label="Lecciones completadas"
          />
          <span className="num">
            {finished} de {lessons.length} lecciones
          </span>
        </div>
        <Practice slug={course.slug} lessons={lessons} done={done} />
        <div className="units">
          {parts.map((part, index) => (
            <Unit
              key={part.title}
              slug={course.slug}
              part={part}
              index={index}
              next={next}
              done={done}
            />
          ))}
        </div>
        {next ? null : (
          <p className="complete">
            Completaste el curso. Repasa cuando quieras.
          </p>
        )}
        <p className="outcome">{course.outcome}</p>
        {finished > 0 ? <ReviewCard slug={course.slug} /> : null}
        {project ? (
          <ProjectTrack slug={course.slug} project={project} parts={parts} />
        ) : null}
      </div>
    </Layout>
  );
}
