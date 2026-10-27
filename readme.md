# Duo

Duo es una plataforma de cursos para aprender haciendo, publicada en
`edu.rising.sh`. Un catálogo en `/` lista los cursos y cada curso es una carpeta
de `site/`. La plataforma pone lo que los cursos comparten: el tema, las cuentas
con su progreso y la ejecución de código en el navegador.

El único curso es **Qiskit**, en `/qiskit/`: lecciones narradas con animaciones,
ejercicios de código que se comprueban en la página, cuadernos de práctica y un
proyecto que crece parte por parte. Las lecciones son una página estática; los
cuadernos usan el entorno de Python del proyecto.

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

Abre <http://localhost:8810/>: es el catálogo. El curso de Qiskit está en
<http://localhost:8810/qiskit/>, y una lección se abre en
`qiskit/lesson.html?l=<id>`, por ejemplo
<http://localhost:8810/qiskit/lesson.html?l=p1-quickstart>. La página no
necesita internet. `tools/serve.py` sirve `site/` y corrige los ejercicios de
código en tu equipo, sin cuentas.

## Abrir un cuaderno de práctica

```sh
uv run marimo edit practica/p1-quickstart.py
```

Es el cuaderno de la misión de la lección `p1-quickstart`. Los cuadernos están
en [`practica/`](practica/).

## Añadir un curso

1. Crea `site/<curso>/` con su `index.html` y un `course.json` con `parts`, la
   lista de partes, cada una con su lista `lessons`. El catálogo cuenta las
   lecciones con ese archivo.
2. Añade una entrada a `site/courses.json` con `slug` (el nombre de la carpeta),
   `title`, `summary` y `language`.
3. Enlaza `../theme.css` y `../theme.js` desde las páginas del curso, y llama a
   las rutas de la plataforma por su ruta absoluta (`/api/me`, `/run`).

No hay que cambiar el código de la plataforma.

## Comprobar

```sh
mise run check
```

Ejecuta `lint`, `typecheck`, `test` y `build`, y no escribe nada versionado.
`mise run fix` aplica los arreglos seguros y el formato, y `mise run generate`
reescribe los archivos generados que `build` encuentra desactualizados.
`mise run test:integration` construye la imagen del corredor y necesita Docker,
por eso `check` no lo ejecuta. La definición de cada paso está en
[`mise.toml`](mise.toml).

## Desplegar

El sitio se publica como un Worker de Cloudflare con un contenedor para ejecutar
código. [docs/deploy.md](docs/deploy.md) lleva paso a paso a quien bifurca el
repositorio hasta su propia copia.

## Más

[docs/readme.md](docs/readme.md) es el índice de la documentación.
