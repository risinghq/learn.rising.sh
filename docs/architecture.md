# Arquitectura

Duo es una página estática (`site/`) con un catálogo de cursos y un Worker de
Cloudflare que atiende lo que los cursos comparten: las cuentas, el progreso y
la ejecución de código. Este documento dice qué hay en cada carpeta y por dónde
pasa una petición.

## Carpetas

| Carpeta        | Contenido                                                                                        |
| -------------- | ------------------------------------------------------------------------------------------------ |
| `site/`        | La página estática: el catálogo, el tema común y una carpeta por curso. [Detalle](#site)         |
| `lessons_src/` | Las lecciones del curso de Qiskit como código Python y el programa que las convierte en JSON.    |
| `practica/`    | Los cuadernos marimo de las misiones, el proyecto y sus soluciones.                              |
| `exercises/`   | Los ejercicios de código: código inicial, solución y casos de cada uno.                          |
| `qgcheck/`     | El corrector de ejercicios: ejecuta el código de un alumno y devuelve el resultado de cada caso. |
| `runner/`      | La imagen del corredor (`server.py`, `sandbox.py`) y el Worker (`worker/`).                      |
| `editor/`      | El paquete que compila `site/qiskit/editor.js` y copia KaTeX y las tipografías a `site/vendor/`. |
| `content/`     | La caché de la síntesis de voz.                                                                  |
| `tools/`       | Programas auxiliares: guías originales, narración, comprobaciones, servidor local y panel.       |
| `tests/`       | Pruebas de navegador, de ejercicios, del corredor y del panel.                                   |
| `stubs/`       | Tipos de `qiskit` y `qiskit_aer` para mypy.                                                      |

Cada parte tiene su documento:

| Parte                             | Documento                      |
| --------------------------------- | ------------------------------ |
| `lessons_src/`, `practica/`       | [lessons.md](lessons.md)       |
| `exercises/`, `qgcheck/`          | [exercises.md](exercises.md)   |
| `runner/` (imagen)                | [runner.md](runner.md)         |
| `runner/worker/` (cuentas)        | [accounts.md](accounts.md)     |
| `runner/worker/` (límites, gasto) | [protection.md](protection.md) |
| Tema de `site/`                   | [design.md](design.md)         |
| Publicar                          | [deploy.md](deploy.md)         |

## `site/`

En la raíz están el catálogo y lo que comparten los cursos:

- `index.html` y `catalog.css` son el catálogo, en inglés. Lee `courses.json`,
  con una entrada por curso (`slug`, `title`, `summary`, `language`), y de cada
  `<slug>/course.json` el número de lecciones. Dibuja una tarjeta por curso con
  un enlace a `<slug>/`.
- `theme.css` y `theme.js` son el tema del catálogo y de los cursos
  ([design.md](design.md)).
- `vendor/` son KaTeX y las dos tipografías, copiados de `editor/node_modules`
  por `editor/vendor.js`. Git los ignora; `mise run install` y `mise run deploy`
  los generan. Ninguna página pide nada a otro sitio salvo el script de
  Turnstile, que `exercise.js` descarga de Cloudflare cuando el corredor lo
  exige.

`qiskit/` es el curso de Qiskit. Sus páginas enlazan el tema y `vendor/` con
`../`, y llaman a las rutas de la plataforma por su ruta absoluta:

- `index.html` es la portada del curso, con los estilos de `index.css`. Lee
  `course.json` y pide los `lesson.json` de las lecciones completadas para armar
  el repaso.
- `lesson.html` carga `engine.js`, el reproductor, con los estilos de `app.css`.
  `blocks.js` dibuja los bloques propios del curso, `exercise.js` el bloque de
  ejercicio y `sfx.js` los sonidos. KaTeX dibuja las fórmulas.
- `account.js` es el menú de la cuenta y `privacidad.html` la página que dice
  qué se guarda ([accounts.md](accounts.md#en-el-sitio)).
- `editor.js` es el editor CodeMirror 6 de los ejercicios, empaquetado desde
  `editor/` ([exercises.md](exercises.md#reconstruir-el-editor)).
- `notebooks.js` escribe la línea «cómo ejecutar los cuadernos» que acompaña a
  cada comando de `marimo`.
- `lessons/<id>/` contiene `lesson.json`, `timings.json` y `audio/<paso>.mp3`.
- `course.json` es el índice: partes, lecciones, minutos y misiones.

## Una petición

Un solo Worker, `duo`, sirve `site/` como archivos estáticos y atiende cuatro
rutas antes que los archivos:

| Ruta      | Quién la atiende                                                                                                   |
| --------- | ------------------------------------------------------------------------------------------------------------------ |
| `/run`    | El Worker comprueba la petición ([protection.md](protection.md)) y la pasa al contenedor ([runner.md](runner.md)). |
| `/auth/*` | El inicio de sesión ([accounts.md](accounts.md#entrar)).                                                           |
| `/api/*`  | La cuenta y su progreso ([accounts.md](accounts.md#el-progreso)).                                                  |
| `/health` | El Worker, sin tocar el contenedor.                                                                                |

En tu equipo no hay Worker: `tools/serve.py` sirve `site/` y responde `/run` con
`qgcheck`, sin cuentas ni límites
([exercises.md](exercises.md#dónde-corre-el-código)).
