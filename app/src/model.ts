// What a page needs, read from site/courses.json and each course's files when the pages are built.

export interface Mission {
  notebook: string;
  title: string;
  tasks: number;
}

export interface Lesson {
  id: string;
  section: string;
  title: string;
  summary: string;
  minutes: number;
  missions?: Mission[];
}

export interface Part {
  title: string;
  desc: string;
  lessons: Lesson[];
}

export interface Source {
  label: string;
  url: string;
  license: string;
}

export interface Course {
  slug: string;
  title: string;
  outcome: string;
  source?: Source;
  note?: string;
}

export interface Milestone {
  n: number;
  part: number;
  title: string;
  desc: string;
  notebook: string;
}

export interface Project {
  title: string;
  tagline: string;
  milestones: Milestone[];
}

export interface CatalogPage {
  kind: "catalog";
  courses: {
    course: Course;
    lessons: Pick<Lesson, "id" | "section" | "title" | "minutes">[];
  }[];
}

export interface CoursePage {
  kind: "course";
  course: Course;
  parts: Part[];
  project?: Project;
}

export interface PrivacyPage {
  kind: "privacy";
}

/** The drill session of a course, played at `/<slug>/repaso/`. */
export interface SessionPage {
  kind: "session";
  course: Course;
}

export type Page = CatalogPage | CoursePage | PrivacyPage | SessionPage;
