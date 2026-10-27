# Lecciones y cuadernos

Una lección del curso de Qiskit es una secuencia de pasos con voz, subtítulos,
animaciones, código y preguntas. Se escribe en Python (`lessons_src/`), se
convierte en JSON y la reproduce `engine.js`. La práctica son cuadernos marimo
(`practica/`) y ejercicios de código ([exercises.md](exercises.md)).

## De la fuente al navegador

```text
plan.py + parte*.py -> build.py -> lesson.json (y course.json)
lesson.json -> tts.py -> audio/<paso>.mp3 + timings.json
lesson.json + timings.json + audio -> engine.js
```

- `plan.py` define `PARTS`: las diez partes, el orden de las lecciones y qué
  guías originales cubre cada una. Una guía aparece en exactamente una lección.
- `parte1.py` a `parte10.py` definen `LESSONS`, la lista de lecciones de cada
  parte, con las funciones de `lib.py`: `lesson()`, `beat()`, los bloques
  (`Code`, `Out`, `Circ`, `Hist`…), las acciones (`A`) y las preguntas
  (`choice`, `numeric`, `reveal`, `predict`, `reflect`).
- `build.py` une el plan con las lecciones y escribe los JSON de `site/qiskit/`.
  Numera las secciones según `plan.PARTS`, añade a cada lección el enlace a sus
  guías originales y completa cada bloque `Exercise` con lo que el sitio puede
  mostrar de `exercises/`. `course.json` suma los minutos: la duración de
  `timings.json` si existe, o una estimación por palabras si no, más 45 s por
  pregunta. Antes comprueba que cada guía del índice de Qiskit/documentation
  esté en el plan, que no haya marcas `[[nombre]]` repetidas en una narración y
  que cada acción apunte a una marca y a un objeto que existan. Falla si una
  lección del plan no tiene módulo o si un módulo define una lección que el plan
  no menciona.
- `tts.py` lee `lesson.json`. Por cada paso aplica `pronunciacion.py` al texto
  de `say`, sintetiza `audio/<paso>.mp3` con Edge TTS y mide su duración con
  `ffprobe`. `timings.json` guarda por paso `dur` (segundos), `marks` (el
  segundo en que empieza la palabra que sigue a cada `[[marca]]`) y `cues` (los
  subtítulos con su segundo de inicio). `content/<id>.cache.json` guarda por
  clip el hash de lo que se dijo y los tiempos de cada palabra, para no volver a
  sintetizar un clip que no cambió.
- `engine.js` carga `lesson.json` y `timings.json`, reproduce el audio de cada
  paso y lanza cada acción de `actions` en el segundo de su marca. Los
  subtítulos salen de `cues`. `?beat=N` muestra el estado final del paso N sin
  audio.

Para regenerar tras editar una lección:

```sh
uv run python tools/fetch_docs.py
uv run python lessons_src/build.py
uv run python lessons_src/build.py --tts
```

`fetch_docs.py` descarga las guías originales a `.cache/qiskit-docs`, en la
versión que fija `tools/qiskit-docs.commit` (solo hace falta la primera vez).
`--tts` necesita red (Edge TTS) y `ffprobe`, que viene con ffmpeg. Para
actualizar las guías se cambia el hash de `qiskit-docs.commit`, se ejecuta
`fetch_docs.py` y se corrige `plan.py` hasta que `build.py` pase.

## Programas de `tools/`

| Programa                                             | Función                                                                                                                             |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Descarga `docs/guides` de Qiskit/documentation a `.cache/qiskit-docs`.                                                              |
| `extract.py`                                         | Convierte esas guías en texto plano en `.cache/qiskit-docs/text`.                                                                   |
| `tts.py`                                             | Sintetiza la narración de una lección y escribe `timings.json`.                                                                     |
| `pronunciacion.py`                                   | Diccionario que reescribe siglas y nombres en inglés para que la voz los lea bien.                                                  |
| `verify.py`                                          | Ejecuta el Python de las lecciones, salvo `norun`, y compara los `Out(…, check=True)`.                                              |
| `practica.py`                                        | Ejecuta cada cuaderno con y sin soluciones. También prueba `mo.ui.slider`/`number` en mínimo y máximo. Un error de ejecución falla. |
| `exercises.py`                                       | Corre la solución y el código inicial de cada ejercicio con `qgcheck` y comprueba su `needs`.                                       |
| `serve.py`                                           | Sirve `site/` en local y responde `POST /run`.                                                                                      |
| `dashboard.py`                                       | El panel del operador ([accounts.md](accounts.md#dónde-se-atascan-los-alumnos)).                                                    |
| `playtest.py`, `seektest.py`, `shot.py`, `review.py` | Pruebas y capturas con Playwright sobre el curso servido en el puerto 8810.                                                         |

## El ciclo de una lección

Cada lección lleva a actuar y a reflexionar, no solo a ver:

1. **Predecir.** Antes de ver un resultado, el alumno apuesta una respuesta
   (`predict`). La apuesta no se cambia después.
2. **Ver.** La animación narrada.
3. **Hacer.** Una misión ([`Mission`](#misiones-y-cuadernos)) con el cuaderno de
   la lección, o un [ejercicio de código](exercises.md) que se comprueba en la
   propia página.
4. **Reflexionar.** Preguntas abiertas (`reflect`). El texto se guarda en el
   navegador (`qiskit:reflect`) y se ve al volver.
5. **Resumir.** El resumen de la lección.

## Misiones y cuadernos

Una misión nombra un cuaderno de `practica/` y sus tareas, cada una con un
nivel: 🟢 1 reproducir, 🟡 2 modificar, 🔴 3 crear. Cada tarea tiene su
comprobación en el cuaderno. Un [ejercicio de código](exercises.md) usa los
mismos tres niveles en su campo `level`.

Los cuadernos son los `.py` de `practica/` que contienen `marimo.App(`. Se abren
con `uv run marimo edit practica/<id>.py`. Qiskit no corre en el navegador, así
que los cuadernos corren en tu equipo, con el entorno de Python del proyecto.

marimo y no Jupyter porque es reactivo: al cambiar algo todo se recalcula, así
que las comprobaciones dicen ✅ o ❌ al instante y los controles deslizantes
sirven para explorar parámetros. Sus archivos son `.py` normales, fáciles de
versionar y de comprobar con `tools/practica.py`. Las guías de IBM y la
comunidad usan Jupyter, por eso una misión de la parte I enseña a convertir
entre los dos formatos con `marimo convert`.

Un cuaderno puede importar un módulo de su carpeta (`proyecto/ising.py`) porque
`tools/practica.py` pone esa carpeta en `sys.path`.
`practica/soluciones/<cuaderno>.json` (con `__` en lugar de `/` para los
cuadernos de subcarpetas) guarda los pares (texto, reemplazo) que
`tools/practica.py` aplica para comprobar que todas las verificaciones dan ✅.

## El proyecto de la cadena de espines

Un solo experimento crece parte por parte: la magnetización de una cadena de
espines de Ising tras un cambio brusco del campo. Hay un hito por parte, en
`practica/proyecto/hito<N>.py` (N de 1 a 10), y un módulo común,
`practica/proyecto/ising.py`. Los títulos y las descripciones de los hitos están
en `HITOS`, en `site/qiskit/index.html`, que los muestra en la portada del curso
con su estado (guardado en `qiskit:hitos`). Los hitos que ejecutan en un QPU
real piden una cuenta de IBM Quantum.

## Repaso espaciado

La portada del curso propone cada día 3 preguntas de las lecciones completadas
(las `choice` y `numeric`), espaciadas 1, 3, 7 y 21 días. Una pregunta que se
falla vuelve al día siguiente. El estado está en `qiskit:repaso`.
