// These routes go through the Worker before the files of site/. The static file
// service serves all the others without invoking the Worker.
export const WORKER_FIRST = ["/run", "/health", "/auth/*", "/api/*"];
