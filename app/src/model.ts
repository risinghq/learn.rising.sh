// What a page needs, read from site/courses.json and each course's files when the pages are built.

export interface Lesson {
  id: string;
  section: string;
  title: string;
  summary: string;
  minutes: number;
}

export interface Part {
  title: string;
  desc: string;
  lessons: Lesson[];
}

export type Guide = Lesson;

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
  lesson: string;
  exercise: string;
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
  guides: Guide[];
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

export interface FriendsPage {
  kind: "friends";
}

export type Page =
  | CatalogPage
  | CoursePage
  | FriendsPage
  | PrivacyPage
  | SessionPage;
