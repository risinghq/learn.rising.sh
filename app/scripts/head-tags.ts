import type { Page } from "../src/model.ts";

// The sRGB of --n1 in the light and the dark theme, for the colour of the browser bar.
const LIGHT = "#fcfbfe";
const DARK = "#0f0f14";

const escape = (text: string) =>
  text.replace(
    /[&<>"]/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c] as string,
  );

export interface Meta {
  title: string;
  description: string;
}

export function metaOf(page: Page): Meta {
  switch (page.kind) {
    case "catalog":
      return {
        title: "Rising",
        description:
          "Cursos cortos para aprender haciendo, con lecciones narradas y ejercicios que ejecutas en la página.",
      };
    case "course":
      return {
        title: `${page.course.title} · Rising`,
        description: page.course.outcome,
      };
    case "session":
      return {
        title: `Repaso de ${page.course.title} · Rising`,
        description: `Un repaso corto de ${page.course.title}, con ejercicios que respondes con un toque.`,
      };
    case "friends":
      return {
        title: "Amigos · Rising",
        description:
          "Compara tu semana con la de tus amigos y recibe un aviso si tu racha está en juego.",
      };
    case "privacy":
      return {
        title: "Privacidad · Rising",
        description:
          "Qué se guarda de tu progreso, cuánto tiempo y cómo borrarlo.",
      };
  }
}

/** Everything the template's head needs apart from the files Vite hashed. */
export function headTags(
  page: Page,
  fontFile: string,
  revision?: string,
): string {
  const { title, description } = metaOf(page);
  return [
    `<title>${escape(title)}</title>`,
    `<meta name="description" content="${escape(description)}" />`,
    ...(revision
      ? [`<meta name="revision" content="${escape(revision)}" />`]
      : []),
    `<meta name="theme-color" content="${LIGHT}" media="(prefers-color-scheme: light)" />`,
    `<meta name="theme-color" content="${DARK}" media="(prefers-color-scheme: dark)" />`,
    `<link rel="manifest" href="/manifest.webmanifest" />`,
    `<link rel="icon" href="/icons/icon-192.png" type="image/png" />`,
    `<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />`,
    `<link rel="preload" href="${fontFile}" as="font" type="font/woff2" crossorigin />`,
    `<link rel="stylesheet" href="/theme.css" />`,
    `<script src="/theme.js"></script>`,
    `<script src="/account.js"></script>`,
  ].join("\n    ");
}
