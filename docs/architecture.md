# Arquitectura

El curso es una página estática (`site/`) que reproduce lecciones descritas en
JSON. Las lecciones se escriben en Python, el audio se sintetiza aparte y los
cuadernos de práctica son archivos marimo. Este documento dice qué posee cada
carpeta y por dónde pasa una lección.

## Quién posee qué

| Carpeta        | Contenido                                                                                                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `lessons_src/` | Las lecciones como código Python y el programa que las convierte en JSON.                                                                                                      |
| `tools/`       | Programas auxiliares: guías originales, narración, comprobaciones y pruebas de navegador.                                                                                      |
| `site/`        | La página estática: portada, reproductor de lecciones y los datos que lee.                                                                                                     |
| `tests/`       | Pruebas de navegador (`theme_test.py`, `proyecto_test.py`, `exercise_ui_test.py`, `account_ui_test.py`) de ejercicios (`exercises_test.py`) y del corredor (`runner_test.py`). |
| `practica/`    | Los cuadernos marimo de las misiones y sus soluciones.                                                                                                                         |
| `exercises/`   | Los ejercicios de código: código inicial, solución y casos de cada uno.                                                                                                        |
| `editor/`      | El paquete que compila `site/editor.js` y copia KaTeX y las tipografías a `site/vendor/`.                                                                                      |
| `qgcheck/`     | El corrector de ejercicios: lee `exercises/`, ejecuta el código de un alumno y devuelve el resultado de cada caso.                                                             |
| `content/`     | La caché de la síntesis de voz.                                                                                                                                                |
| `runner/`      | El corredor de código del alumno: imagen, servidor `/run` y Worker. [runner.md](runner.md)                                                                                     |

### `lessons_src/`

- `plan.py` define `PARTS`: las diez partes, el orden de las lecciones y qué
  guías originales cubre cada una. Una guía aparece en exactamente una lección.
- `parte1.py` a `parte10.py` definen `LESSONS`, la lista de lecciones de cada
  parte, con las funciones de `lib.py`: `lesson()`, `beat()`, los bloques
  (`Code`, `Out`, `Circ`, `Hist`…), las acciones (`A`) y las preguntas
  (`choice`, `numeric`, `reveal`, `predict`, `reflect`).
- `build.py` une el plan con las lecciones y escribe los JSON de `site/`. Antes
  comprueba que cada guía del índice de Qiskit/documentation esté en el plan,
  que no haya marcas `[[nombre]]` repetidas en una narración y que cada acción
  apunte a una marca y a un objeto que existan. Falla si una lección del plan no
  tiene módulo o si un módulo define una lección que el plan no menciona.
  También completa cada bloque `Exercise` con lo que el sitio puede mostrar de
  `exercises/` (ver [exercises.md](exercises.md)).

### `tools/`

| Programa                                             | Función                                                                                                                             |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `fetch_docs.py`                                      | Descarga `docs/guides` de Qiskit/documentation a `.cache/qiskit-docs`, en la versión de `qiskit-docs.commit`.                       |
| `extract.py`                                         | Convierte esas guías en texto plano en `.cache/qiskit-docs/text`.                                                                   |
| `tts.py`                                             | Sintetiza la narración de una lección y escribe `timings.json`.                                                                     |
| `pronunciacion.py`                                   | Diccionario que reescribe siglas y nombres en inglés para que la voz los lea bien.                                                  |
| `verify.py`                                          | Ejecuta el Python de las lecciones, salvo `norun`, y compara los `Out(…, check=True)`.                                              |
| `practica.py`                                        | Ejecuta cada cuaderno con y sin soluciones. También prueba `mo.ui.slider`/`number` en mínimo y máximo. Un error de ejecución falla. |
| `exercises.py`                                       | Corre la solución y el código inicial de cada ejercicio con `qgcheck` y comprueba su `needs`.                                       |
| `serve.py`                                           | Sirve `site/` en 127.0.0.1:8810 y añade `POST /run`, que corrige un ejercicio con `qgcheck`.                                        |
| `playtest.py`, `seektest.py`, `shot.py`, `review.py` | Pruebas y capturas con Playwright sobre `site/` servido en el puerto 8810.                                                          |

`qiskit-docs.commit` guarda el hash de Qiskit/documentation contra el que se
comprueba la cobertura. Para actualizar las guías se cambia ese hash, se ejecuta
`tools/fetch_docs.py` y se corrige `plan.py` hasta que `build.py` pase.

### `site/`

- `index.html` es la portada, con los estilos de `index.css`. Lee `course.json`
  y pide en paralelo los `lesson.json` de las lecciones completadas para armar
  el repaso.
- `lesson.html` carga `engine.js`, el reproductor, con los estilos de `app.css`.
  `blocks.js` dibuja los bloques propios del curso, `exercise.js` el bloque de
  ejercicio y `sfx.js` los sonidos. Las fórmulas las dibuja KaTeX, que sale de
  `vendor/`. Las dos páginas cargan KaTeX con `defer`, antes que sus propios
  scripts.
- `vendor/` son KaTeX y las tres tipografías, copiados de `editor/node_modules`
  por `editor/vendor.js`. Git los ignora; `mise run install` y `mise run deploy`
  los generan de nuevo y borran antes lo que hubiera. Ninguna página pide nada a
  otro sitio salvo el script de Turnstile, que `exercise.js` descarga de
  Cloudflare cuando el corredor lo exige.
- `editor.js` es el editor CodeMirror 6 de los ejercicios, empaquetado desde
  `editor/`. Se describe en [exercises.md](exercises.md#editor-en-la-lección).
- `theme.css` y `theme.js` son el tema de las dos páginas: colores, fuentes, y
  la paleta y el modo que elige el lector. [design.md](design.md) los describe.
  `notebooks.js` escribe la línea «cómo ejecutar los cuadernos» que acompaña a
  cada comando de `marimo`.
- `lessons/<id>/` contiene `lesson.json`, `timings.json` y `audio/<paso>.mp3`.
- `course.json` es el índice: partes, lecciones, minutos y misiones.

### `practica/`

Los cuadernos marimo son los `.py` de estas carpetas que contienen
`marimo.App(`. Un cuaderno puede importar un módulo de su carpeta
(`proyecto/ising.py`), porque `tools/practica.py` pone esa carpeta en
`sys.path`. Cada misión de una lección nombra su cuaderno con `Mission(...)`.
`soluciones/<cuaderno>.json` (con `__` en lugar de `/` para los cuadernos de
subcarpetas) guarda los pares (texto, reemplazo) que `tools/practica.py` aplica
para comprobar que todas las verificaciones dan ✅.

### `exercises/` y `qgcheck/`

`exercises/<lección>/<ejercicio>/` guarda `starter.py`, `solution.py` y
`check.py`. `qgcheck/spec.py` los localiza, `qgcheck/runner.py` lanza
`qgcheck/job.py` en un proceso aparte (que a su vez lanza `qgcheck/host.py` con
el código del alumno), y `qgcheck/__init__.py` ofrece a `check.py` sus
ayudantes. El formato, el resultado de `grade()` y las comprobaciones están en
[exercises.md](exercises.md). `site/exercise.js` dibuja el editor de cada
ejercicio y llama a `POST /run` en su propio origen.

### `content/`

`<id>.cache.json` guarda, por cada clip de una lección, el hash de lo que se
dijo y los tiempos de cada palabra. `tts.py` lo consulta para no volver a
sintetizar un clip que no cambió.

### `runner/`

El servidor del corredor ([runner.md](runner.md)) ejecuta los trabajos en
_ranuras_. Hay `QG_JOBS` ranuras, numeradas desde 0, y la ranura `n` usa siempre
el uid `20000 + n`. El estado compartido es la cola `FREE_SLOTS` de ranuras
libres, en `server.py`.

| Estado  | Significa                                     | Quién lo deja y cuándo                                                                                            |
| ------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| libre   | Su número está en `FREE_SLOTS`.               | El hilo de una petición, en el `finally` de `do_POST`, cuando `run_job` ya volvió.                                |
| ocupada | Un hilo de petición tiene su número y la usa. | El mismo hilo, tras validar la petición, con `get_nowait()`. Si la cola está vacía responde 503 y no espera nada. |

- Solo el hilo que tomó una ranura la devuelve, y solo después de que `run_job`
  matara los procesos de ese uid y borrara su directorio y sus archivos de
  `/scratch`, `/tmp`, `/var/tmp` y `/dev/shm`. Ese borrado es lo que aísla a un
  trabajo del anterior, porque el uid se reutiliza.
- `run_job` lanza un hilo (`_Scan`) que mide memoria y disco. Solo ese hilo
  escribe `peak` y `killed` (`killed` antes de `tripped`); `run_job` los lee
  tras `tripped` o tras unir el hilo.
- Las instancias de Cloudflare no comparten nada: cada una tiene su cola. El
  Worker elige una de dos y, si responde 503, repite la petición una vez en la
  otra, con su propia reserva del presupuesto.
- El Worker guarda su estado en dos Durable Objects de
  `runner/worker/src/meters.ts` ([runner.md](runner.md#protección-del-worker)
  explica los límites). Cada objeto atiende una llamada a la vez, y sus métodos
  solo esperan a su propio almacenamiento, así que leer y escribir dentro de un
  método es una operación.

`RateLimiter` hay uno por clave (una IP o un usuario), etiqueta y día, nombrado
con un HMAC de los tres. Su estado es el registro `count` (minuto del reloj,
peticiones de ese minuto y del día).

| Estado   | Significa                                | Quién lo deja y cuándo                                                                                                                                               |
| -------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| vacío    | No hay `count`.                          | Al crearse el objeto, y la alarma `alarm` cuando termina el día más un minuto.                                                                                       |
| contando | Hay `count` y una alarma al fin del día. | `take`, que el Worker llama en cada `POST /run` y en cada petición a `/auth` y `/api`. Suma una petición si caben en el minuto y en el día, y si no, no cambia nada. |

- Al cambiar el minuto del reloj, `take` empieza el contador del minuto de cero
  sin esperar a ningún evento. El contador del día sigue hasta la alarma.
- Solo `take` escribe `count`, y solo `alarm` lo borra.

`Budget` hay uno en total. Su estado son tres tipos de registro: `month` y `day`
(periodo UTC y nanodólares gastados; `day` cuenta solo el gasto público) y, por
instancia, `awake:<instancia>` (el instante en que se espera que se apague y la
reserva que lo fijó).

| Estado        | Significa                                                                | Quién lo deja y cuándo                                                                                                                                                                           |
| ------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| periodo nuevo | No hay `month` (o `day`), o su periodo no es el actual: el total es 0.   | El paso del reloj al día 1 UTC, o a un día nuevo. No hay temporizador: el primer `reserve` del periodo nuevo lo sobrescribe.                                                                     |
| reservado     | El total incluye lo apartado por ejecuciones que aún no terminaron.      | `reserve`, que el Worker llama antes de arrancar el contenedor. Suma la reserva solo si caben el tope del mes (el del público o el total) y, para el público, el del día; si no, no cambia nada. |
| ajustado      | El total cambia la reserva por el coste medido, con tope en lo apartado. | `settle`, al terminar la ejecución y, sin coste, cuando Turnstile rechaza una petición que ya había apartado. No hace nada si el periodo ya cambió.                                              |

- `reserve` suma la ventana encendida desde `max(ahora, awakeUntil)` y deja
  `awakeUntil` en `ahora` más la reserva más `sleepAfter`. `settle` solo lo
  acorta si la reserva que lo fijó sigue siendo la dueña; si otra lo alargó, esa
  parte sigue cobrada.
- Una petición tiene una reserva por intento, y cada una se aparta una vez y se
  cambia una vez; o se interrumpe y la reserva se queda en el total.
- Un `settle` que falla se registra y no cambia la respuesta de la petición.

`DB` es la base D1 de las cuentas ([runner.md](runner.md#cuentas) da los
endpoints y [`schema.sql`](../runner/worker/src/schema.sql) las tablas). Todo
cuelga de `users` con `ON DELETE CASCADE`, y D1 hace cumplir las claves
foráneas: borrar un usuario borra todo lo suyo en una sola sentencia. Las
sentencias de un lote de D1 se ejecutan seguidas, sin que otra escritura se
intercale.

Usuario (`users`):

| Estado    | Significa                                                    | Quién lo deja y cuándo                                                                                                                           |
| --------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| no existe | No hay fila con ese id.                                      | El principio; y `DELETE /api/me` o la limpieza diaria, que borran la fila.                                                                       |
| activo    | Hay fila y `seen_day` es el día de la última visita.         | `userForIdentity`, en la vuelta de OAuth de una identidad nueva, en un lote con su fila de `identities`. Cada visita con sesión sube `seen_day`. |
| inactivo  | `seen_day` es anterior a hoy menos `ACCOUNT_RETENTION_DAYS`. | El paso del tiempo. No hay temporizador: la limpieza diaria lo borra.                                                                            |

- Dos primeras entradas a la vez de la misma identidad crean un solo usuario: la
  clave de `identities` es (proveedor, identificador), el lote de la segunda se
  deshace entero y esa entrada usa el usuario de la primera.
- Una visita es una petición con sesión a `/run` o a `/api`, o la vuelta de
  OAuth. `seen_day` solo sube, a lo sumo una vez al día.

Sesión (`sessions`):

| Estado   | Significa                                     | Quién lo deja y cuándo                                                              |
| -------- | --------------------------------------------- | ----------------------------------------------------------------------------------- |
| vigente  | Hay fila y `expires_at` es posterior a ahora. | `openSession`, en la vuelta de OAuth. Cada inicio crea una y deja las anteriores.   |
| caducada | Hay fila y `expires_at` ya pasó.              | El paso del tiempo. `sessionUser` ya no la acepta; la fila sigue hasta la limpieza. |
| cerrada  | No hay fila.                                  | `POST /auth/logout`, la limpieza de las caducadas y el borrado del usuario.         |

Una sesión nunca vuelve a vigente. Una cuenta tiene tantas a la vez como
dispositivos con los que entró.

Progreso (`lesson_done`, `exercise_state`, `kv` y `users.progress_version`):

| Estado    | Significa                              | Quién lo deja y cuándo                                                  |
| --------- | -------------------------------------- | ----------------------------------------------------------------------- |
| vacío     | El usuario no tiene filas en las tres. | La creación del usuario, con `progress_version` 0.                      |
| con datos | Tiene filas en alguna de las tres.     | `mergeProgress`, que sirve a `POST /api/merge` y a `PUT /api/progress`. |

- Una escritura no quita nada: no borra una lección, `passed` no vuelve a falso,
  `hints`, `checks` y `at` solo suben, y el código solo lo cambia una edición
  con `at` mayor. Cada clave de `kv` se junta por la regla de su familia
  ([runner.md](runner.md#el-progreso)). Lo que no cambia el resultado no
  escribe.
- `mergeProgress` lee las tres tablas y `progress_version` en un lote, calcula
  el resultado y lo escribe en otro lote cuyas sentencias solo actúan si
  `progress_version` sigue siendo la leída; la última la sube en uno. Si otra
  escritura del mismo usuario se coló, esa última no cambia ninguna fila y la
  petición vuelve a leer. Tras 10 intentos responde 503 `busy`. Ninguna
  escritura pisa a otra.
- Si el usuario se borra mientras la petición corre, la lectura no lo encuentra
  y responde 401 `signed_out`.

Intento (`attempts`):

| Estado  | Significa                                                | Quién lo deja y cuándo                                                                                    |
| ------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| anotado | Hay fila, con `user_id` o con `NULL`.                    | `recordAttempt`, tras cada respuesta 200 de `/run` cuyo JSON tiene la forma del contrato.                 |
| vencido | `at` es anterior a ahora menos `ATTEMPT_RETENTION_DAYS`. | El paso del tiempo. La limpieza diaria lo borra.                                                          |
| borrado | No hay fila.                                             | La limpieza diaria y, si tenía `user_id`, el borrado del usuario. Los anónimos solo salen en la limpieza. |

Una fila no se modifica después de escribirse.

Borrado y limpieza:

- `DELETE /api/me` borra la fila de `users`. Con ella salen las identidades, las
  sesiones, el progreso y los intentos del usuario. Las peticiones siguientes
  con su cookie ya no encuentran la sesión.
- El cron diario ejecuta `purge` en un lote, en este orden: intentos vencidos,
  sesiones caducadas, usuarios inactivos. Un usuario inactivo que entra justo
  mientras corre puede perder la sesión que abría (500); al reintentar se crea
  una cuenta nueva.

## Camino de los datos

```text
plan.py + parte*.py -> build.py -> lesson.json (y course.json)
lesson.json -> tts.py -> audio/<paso>.mp3 + timings.json
lesson.json + timings.json + audio -> engine.js
```

1. `build.py` numera las secciones según el orden de `plan.PARTS`, añade a cada
   lección el enlace a sus guías originales y escribe `lesson.json` con la lista
   de pasos y `next`, la lección siguiente. `course.json` suma los minutos: la
   duración de `timings.json` si existe, o una estimación por palabras si no,
   más 45 segundos por pregunta.
2. `tts.py` lee `lesson.json`. Por cada paso aplica `pronunciacion.py` al texto
   de `say`, sintetiza `audio/<paso>.mp3` con Edge TTS y mide su duración con
   `ffprobe`. `timings.json` guarda por paso `dur` (segundos), `marks` (el
   segundo en que empieza la palabra que sigue a cada `[[marca]]`) y `cues` (los
   subtítulos con su segundo de inicio, con el texto original).
3. `engine.js` carga `lesson.json` y `timings.json`, reproduce el audio de cada
   paso y lanza cada acción de `actions` en el segundo de su marca. Los
   subtítulos salen de `cues`. `?beat=N` muestra el estado final del paso N sin
   audio.
