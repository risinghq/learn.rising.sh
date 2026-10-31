import { ArrowRight } from "lucide-react";

import type { CatalogPage } from "../model.ts";
import { hours, lessonHref, minutesOf, nextLesson } from "../path.ts";
import { useDoneByCourse, useLastCourse } from "../store.ts";
import { Layout } from "./Layout.tsx";

type Entry = CatalogPage["courses"][number];

function primaryOf(
  entries: Entry[],
  done: Record<string, ReadonlySet<string>>,
  last: string | null,
): string | undefined {
  const open = entries.filter(
    (e) => (done[e.course.slug]?.size ?? 0) < e.lessons.length,
  );
  const started = open.filter((e) => done[e.course.slug]?.size);
  return (started.find((e) => e.course.slug === last) ?? started[0] ?? open[0])
    ?.course.slug;
}

function CourseCard({
  entry,
  done,
  primary,
}: {
  entry: Entry;
  done: ReadonlySet<string>;
  primary: boolean;
}) {
  const { course, lessons } = entry;
  const finished = lessons.filter((l) => done.has(l.id)).length;
  const next = nextLesson(lessons, done) ?? lessons[0];
  const label =
    finished === 0
      ? "Empezar"
      : finished === lessons.length
        ? "Repasar"
        : "Continuar";
  return (
    <li className="course-card">
      <h2>
        <a href={`/${course.slug}/`}>{course.title}</a>
      </h2>
      <p>{course.outcome}</p>
      {finished > 0 ? (
        <div className="meter">
          <progress
            max={lessons.length}
            value={finished}
            aria-label={`Progreso de ${course.title}`}
          />
          <span className="num">
            {finished} de {lessons.length} lecciones
          </span>
        </div>
      ) : (
        <p className="meta num">
          {lessons.length} lecciones · {hours(minutesOf(lessons))} h
        </p>
      )}
      <a
        className={primary ? "btn primary" : "btn"}
        href={lessonHref(course.slug, next.id)}
      >
        {label}
        <ArrowRight aria-hidden="true" />
        <span className="sr"> {course.title}</span>
      </a>
    </li>
  );
}

export function Catalog({ page }: { page: CatalogPage }) {
  const done = useDoneByCourse(page.courses.map((e) => e.course.slug));
  const last = useLastCourse();
  const primary = primaryOf(page.courses, done, last);
  const drill = page.courses.find(
    (e) => e.course.slug === (last ?? primary) && done[e.course.slug]?.size,
  )?.course.slug;
  return (
    <Layout stats drill={drill}>
      <div className="page">
        <h1>Tus cursos</h1>
        <ul className="courses">
          {page.courses.map((entry) => (
            <CourseCard
              key={entry.course.slug}
              entry={entry}
              done={done[entry.course.slug]}
              primary={entry.course.slug === primary}
            />
          ))}
        </ul>
        <p>
          <a href="/amigos/">Amigos y tablero de la semana</a>
        </p>
      </div>
    </Layout>
  );
}
