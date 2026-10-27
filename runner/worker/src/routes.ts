// Las rutas de la plataforma sirven a todos los cursos y están en la raíz del host.
export const PLATFORM_ROUTES = ["/run", "/health", "/auth/*", "/api/*"];

// Estas rutas conservan los enlaces del curso de Qiskit que apuntaban a la raíz.
const LEGACY_COURSE = "qiskit";
const LEGACY_PAGES = ["/", "/index.html", "/lesson.html", "/privacidad.html"];
const LEGACY_LESSONS = "/lessons/";

// Estas rutas pasan por el Worker antes que los archivos de site/: las de la
// plataforma, y las antiguas del curso, que el Worker redirige solo en el host
// antiguo (`legacyRedirect`) y en cualquier otro pasa a los archivos.
// Las demás las responde el servicio de archivos estático.
export const WORKER_FIRST = [
  ...PLATFORM_ROUTES,
  ...LEGACY_PAGES,
  `${LEGACY_LESSONS}*`,
];

// Devuelve un 301 para una página del curso en `legacyHost` cuando la petición
// usa GET o HEAD. Devuelve null para otras rutas o métodos.
export function legacyRedirect(
  request: Request,
  legacyHost: string,
  homeHost: string,
): Response | null {
  const url = new URL(request.url);
  if (!legacyHost || url.hostname !== legacyHost) return null;
  if (request.method !== "GET" && request.method !== "HEAD") return null;
  const course = `https://${homeHost}/${LEGACY_COURSE}/`;
  let target: string;
  if (url.pathname === "/" || url.pathname === "/index.html") {
    target = course;
  } else if (
    LEGACY_PAGES.includes(url.pathname) ||
    url.pathname.startsWith(LEGACY_LESSONS)
  ) {
    target = course + url.pathname.slice(1);
  } else {
    return null;
  }
  return new Response(null, {
    status: 301,
    headers: { Location: target + url.search },
  });
}
