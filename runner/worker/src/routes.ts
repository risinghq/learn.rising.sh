// Estas rutas pasan por el Worker antes que los archivos de site/. Las demás las
// sirve el servicio de archivos estáticos sin invocar el Worker.
export const WORKER_FIRST = ["/run", "/health", "/auth/*", "/api/*"];
