# Duo

Duo es la plataforma de aprendizaje de Rising, publicada en `edu.rising.sh`. Un
catálogo en `/` lista los cursos y cada curso vive en su carpeta de `site/`. La
plataforma pone lo que comparten todos: el tema, las cuentas y el progreso, y la
ejecución de código (`/auth/*`, `/api/*`, `/run`, `/health`).

Hoy hay un curso: **Qiskit en español**, en `/qiskit/`. Son 67 lecciones en diez
partes, narradas y con animaciones, sobre las guías de IBM Quantum y Qiskit,
desde qué es Qiskit hasta organizaciones y seguridad. Cada lección es una
secuencia de pasos con voz, subtítulos, código que se ejecuta y preguntas.
Algunas traen una misión en un cuaderno de práctica.

Todo corre en tu equipo: las lecciones son una página estática y los cuadernos
usan el entorno de Python del proyecto.

## Añadir un curso

1. Crea `site/<curso>/` con su `index.html` y un `course.json` con `parts`, la
   lista de partes, cada una con su lista `lessons`. El catálogo cuenta las
   lecciones con ese archivo.
2. Añade una entrada a `site/courses.json` con `slug` (el nombre de la carpeta),
   `title`, `summary` y `language`.
3. Enlaza `../theme.css` y `../theme.js` desde las páginas del curso, y llama a
   las rutas de la plataforma por su ruta absoluta (`/api/me`, `/run`).

No hay que cambiar el código de la plataforma.

## Instalar

Necesitas [mise](https://mise.jdx.dev/). `mise.toml` fija las versiones de
Python, uv, Node, Bun y gitleaks, y mise las instala.

```sh
mise run install
```

Instala las dependencias de Python y de JavaScript desde sus archivos de
bloqueo, copia KaTeX y las tipografías a `site/vendor/`, y descarga el Chromium
de Playwright y las guías originales de Qiskit.

## Ver el curso

```sh
uv run python tools/serve.py
```

Abre <http://localhost:8810/>: es el catálogo de cursos. El curso de Qiskit está
en <http://localhost:8810/qiskit/>, y su portada muestra las lecciones por parte
y tu progreso. Una lección se abre en `qiskit/lesson.html?l=<id>`, por ejemplo
<http://localhost:8810/qiskit/lesson.html?l=p1-quickstart>. Las fórmulas y las
tipografías salen del propio sitio, así que la página no necesita internet.
`tools/serve.py` sirve `site/` y además corrige los ejercicios de código de las
lecciones; ver [docs/exercises.md](docs/exercises.md).

## Abrir un cuaderno de práctica

```sh
uv run marimo edit practica/p1-quickstart.py
```

Es el comando que muestra la misión de la lección 1.4. Los cuadernos están en
[`practica/`](practica/) y sus soluciones, para `tools/practica.py`, en
`practica/soluciones/`.

## Reconstruir las lecciones y la narración

Las lecciones se escriben en [`lessons_src/`](lessons_src/). Después de
editarlas:

```sh
uv run python tools/fetch_docs.py
uv run python lessons_src/build.py
```

El primer comando descarga las guías originales de Qiskit a `.cache/` (solo la
primera vez). El segundo regenera `site/qiskit/lessons/<id>/lesson.json` y
`site/qiskit/course.json`, y comprueba que cada guía original tenga lección.

Para generar también el audio y los tiempos:

```sh
uv run python lessons_src/build.py --tts
```

Necesita red (Edge TTS) y `ffprobe` (viene con ffmpeg). Solo se sintetizan los
clips cuyo texto cambió.

## Comprobar

```sh
mise run check
```

Ejecuta `lint`, `typecheck`, `test` y `build`, y no escribe nada versionado:

- `lint` revisa Python con ruff, JavaScript y TypeScript con oxlint, el formato
  de Markdown, JSON, YAML, JavaScript y TypeScript con oxfmt, y busca secretos
  con gitleaks. `mise run fix` aplica los arreglos seguros y el formato.
- `typecheck` pasa mypy en modo estricto sobre Python y `tsc` sobre el Worker.
- `test` ejecuta los cuadernos con y sin sus soluciones, corrige los ejercicios
  de código, prueba el Worker, recorre el sitio con un navegador y ejecuta el
  código Python que muestran las lecciones.
- `build` falla si los JSON de `site/qiskit/` o `site/qiskit/editor.js` no
  coinciden con lo que generan `build.py` y esbuild. `mise run generate` los
  reescribe.

`mise run test:integration` construye la imagen del corredor y necesita Docker,
por eso `check` no lo ejecuta. La definición de cada paso está en
[`mise.toml`](mise.toml).

## Más

[`docs/architecture.md`](docs/architecture.md) explica qué contiene cada carpeta
y cómo llega una lección desde su código fuente hasta el navegador.
[`docs/exercises.md`](docs/exercises.md) describe cómo se escribe y se corrige
un ejercicio de código.
