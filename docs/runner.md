# El corredor de código

El corredor ejecuta el código de un alumno con Qiskit y Qiskit Aer y devuelve lo
que imprimió y el resultado de los casos de un ejercicio, con el formato de
[`qgcheck.grade`](exercises.md#corregir-código). Es una imagen de contenedor con
un servidor HTTP. No depende del anfitrión: el mismo contrato vale en Cloudflare
Containers y en Docker. Es el `POST /run` que llama el editor de las lecciones,
con aislamiento para exponerlo en red; `tools/serve.py` lo responde en tu equipo
sin él.

## Contrato

`POST /run` con un JSON:

| Campo      | Tipo  | Significado                                                                            |
| ---------- | ----- | -------------------------------------------------------------------------------------- |
| `code`     | texto | El código del alumno, hasta 20 000 bytes.                                              |
| `mode`     | texto | `run` (por defecto) ejecuta el código. `check` además lo prueba con el ejercicio.      |
| `exercise` | texto | `lección/ejercicio`, por ejemplo `p1-quickstart/ghz`. Obligatorio con `mode: "check"`. |

Responde 200 con:

```json
{
  "passed": false,
  "stdout": "",
  "error": null,
  "tests": [
    {
      "name": "n = 2, 3 y 4",
      "visible": true,
      "passed": false,
      "message": "Con n = 2 salen ['00'], y deberían salir solo 00 y 11.",
      "hint": 1
    },
    {
      "name": "caso oculto 1",
      "visible": false,
      "passed": false,
      "message": "Con otros tamaños de n no salen solo 00…0 y 11…1.",
      "hint": null
    }
  ],
  "ms": 2438,
  "killed": null,
  "peak_mb": 169
}
```

- `passed` es verdadero si `error` es `null` y, con `check`, hay al menos un
  caso y todos pasan.
- `stdout` junta la salida estándar y la de errores, en el orden en que se
  escribieron. Con `check` es la del código del alumno al cargarse, una vez, y
  la que imprimen sus funciones.
- `error` es el error del código del alumno, con su línea, o el motivo por el
  que el corredor lo detuvo. Con un error, `tests` está vacío.
- `tests` está vacío con `mode: "run"`. Un caso oculto se llama `caso oculto N`.
  `hint` es el número de la pista que nombra el caso, o `null`
  ([exercises.md](exercises.md)).
- `killed` es `time`, `memory`, `disk` u `output` cuando el corredor mató el
  trabajo por ese límite, y `null` si no. Es `scan` si falló la lectura de
  memoria o disco que vigila los límites: sin poder medir, el corredor mata el
  trabajo en vez de dejarlo correr sin tope, y escribe el error en su salida.
- `ms` es el tiempo del trabajo dentro del corredor. `peak_mb` es la mayor suma
  de la memoria proporcional (PSS) de los procesos del trabajo, medida cada 0,5
  s y cuando la memoria residente pasa del tope: una página compartida entre
  procesos se reparte entre ellos, así que cuenta una vez.

Otras respuestas llevan `{"error": "..."}`: 400 si la petición no es válida, 404
si el ejercicio no existe, 413 si el código pasa de 20 000 bytes o el cuerpo de
121 024 (seis veces el código, que es lo que ocupa un carácter de control en
JSON, más la envoltura) y 503 si no queda una ranura libre. `GET /health`
responde 200.

## Límites

| Límite                | Valor              | Cómo se aplica                                                               |
| --------------------- | ------------------ | ---------------------------------------------------------------------------- |
| Tiempo                | 10 s               | `sandbox.py` mata el grupo de procesos y todo proceso del mismo uid.         |
| Memoria               | 512 MB             | `sandbox.py` vigila cada 20 ms y mata si la memoria proporcional (PSS) pasa. |
| Directorio de trabajo | 64 MB              | `sandbox.py` mide el disco cada 100 ms; un archivo no pasa de 16 MB.         |
| Procesos e hilos      | 64                 | `RLIMIT_NPROC` sobre el uid de la ranura.                                    |
| Salida                | 64 KiB             | `sandbox.py` mata el trabajo al pasarse.                                     |
| Red                   | solo `AF_UNIX`     | Un filtro seccomp de `launcher.py` niega `socket` de cualquier otra familia. |
| Escritura             | solo su directorio | Un uid sin privilegios; `/scratch`, `/tmp` y `/app` son de root.             |

Un trabajo corre con el uid de su ranura, sin capacidades y con `no_new_privs`.
Al terminar se matan los procesos de ese uid y se borran su directorio y lo que
dejó en `/scratch`, `/tmp`, `/var/tmp` y `/dev/shm`. El servidor ejecuta tantos
trabajos a la vez como ranuras tiene (`QG_JOBS`, por defecto 1); el ciclo de las
ranuras está en [architecture.md](architecture.md#runner). Los demás valores se
cambian con `QG_WALL_S`, `QG_MEM_MB` y `QG_SCRATCH_MB`.

El trabajo es `python -u -P -m qgcheck.job`, el mismo que lanza
[`qgcheck.grade`](exercises.md#corregir-código) en tu equipo sin los límites de
arriba. Con `mode: "run"` el código del alumno corre en ese proceso. Con
`mode: "check"` hay dos procesos del mismo uid:

- El comprobador (`qgcheck/job.py`) corre los casos de `check.py`. Antes de
  importar nada instala el filtro de importaciones diferidas de Python
  (`sys.set_lazy_imports_filter`) para `qiskit_ibm_runtime` y
  `qiskit_mitigation`: sus clientes y `scipy` se cargan al usarlos, no al
  importar el paquete. Después se declara no volcable e importa las bibliotecas
  de `PRELOAD_ROOTS` (`qgcheck/source.py`) que usan el código del alumno y
  `check.py`.
- El proceso del alumno (`qgcheck/host.py`) es un `fork` del comprobador, hecho
  antes de leer `check.py`, así que hereda las bibliotecas ya cargadas y ninguna
  respuesta. Cierra todos los descriptores salvo su extremo de un `socketpair`
  con el comprobador, ejecuta el código del alumno una vez y atiende las
  peticiones una a una en ese mismo proceso: el estado de nivel superior pasa de
  una a otra, como en el intérprete del alumno, y su salida se muestra una vez.
  No bifurca por petición porque el código del alumno ya puede haber creado
  hilos (Qiskit los crea al transpilar) y el hijo de un proceso con hilos se
  bloquea.

Cada acceso a `learner.<nombre>` de un caso es una petición por el socket: qué
nombres hay, el valor de uno o su llamada. Los mensajes son JSON con la longitud
delante (`qgcheck/wire.py`, hasta 4 MiB) y llevan un `id` que el comprobador
sortea en cada petición. Solo viajan datos: números, textos, listas, tuplas,
diccionarios con claves de texto, `bytes`, arreglos de NumPy, `Statevector`,
`Operator`, `SparsePauliOp` y `QuantumCircuit` en QPY. Nunca se deserializa
código. Un caso que necesita pasar o recibir otra cosa (una clase, un
`PassManager`, un `Target`, unos ejes) la maneja en una función de `check.py`
marcada con `@inside`, que corre en el proceso del alumno y devuelve datos
([exercises.md](exercises.md#escribir-checkpy)).

El comprobador se declara no volcable y el proceso del alumno nace de él antes
de que exista ningún valor esperado, así que el alumno no lee ni escribe la
memoria del comprobador ni abre sus descriptores, y su único canal es el socket.
El alumno decide el valor que devuelve cada petición, lo calcule su función o
no, y los casos juzgan ese valor fuera de su proceso. Como no conoce el `id`
hasta recibir la petición, no puede dejar respuestas escritas para las
siguientes: el comprobador descarta toda respuesta que no repita el `id` y la
trata como un canal roto. El alumno sí puede leer `check.py`: el corredor
protege el anfitrión y la corrección, no la clave de respuestas.

## Archivos

| Archivo                              | Función                                                                                        |
| ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `runner/server.py`                   | El servidor HTTP y la validación de la petición.                                               |
| `runner/sandbox.py`                  | Lanza el trabajo y vigila tiempo, memoria, disco y salida.                                     |
| `runner/launcher.py`                 | Fija los rlimits, baja de uid e instala el filtro seccomp antes del `exec`.                    |
| `qgcheck/job.py`                     | El trabajo: el comprobador de `check` y la ejecución de `run`.                                 |
| `qgcheck/host.py`                    | El proceso del alumno de `check`.                                                              |
| `qgcheck/wire.py`                    | El formato de mensajes entre esos dos procesos.                                                |
| `qgcheck/`                           | El corrector de [exercises.md](exercises.md). La imagen lo copia sin cambios.                  |
| `runner/Dockerfile`                  | La imagen. Python y uv salen de `mise.toml`; las bibliotecas, del grupo `runner` de `uv.lock`. |
| `runner/local.py`                    | Construye la imagen y la ejecuta con Docker y las banderas de aislamiento.                     |
| `runner/bench.py`                    | Mide la latencia fría y templada.                                                              |
| `runner/worker/`                     | El Worker de Cloudflare: sirve `site/` y arranca la imagen como Container.                     |
| `runner/worker/cloudflare.config.ts` | El Worker, el Container, los Durable Objects, las variables y las rutas.                       |
| `runner/worker/wrangler.config.ts`   | El directorio de `site/` que el Worker publica como archivos estáticos.                        |
| `runner/worker/src/routes.ts`        | Las rutas que entran al Worker antes que a los archivos.                                       |
| `runner/worker/src/index.ts`         | Las comprobaciones de [Protección del Worker](#protección-del-worker).                         |
| `runner/worker/src/meters.ts`        | Los Durable Objects `RateLimiter` y `Budget`.                                                  |
| `runner/worker/src/session.ts`       | La cookie de sesión de Turnstile y la llamada a `siteverify`.                                  |
| `runner/worker/src/throttle.ts`      | El contador por clave (IP o usuario) sobre `RateLimiter`.                                      |
| `runner/worker/src/auth.ts`          | `/auth/*`: el inicio de sesión con Google y GitHub y el cierre.                                |
| `runner/worker/src/account.ts`       | Usuarios, identidades y sesiones de cuenta en D1.                                              |
| `runner/worker/src/api.ts`           | `/api/*`: la cuenta y su progreso.                                                             |
| `runner/worker/src/progress.ts`      | La validación y la unión del progreso.                                                         |
| `runner/worker/src/attempts.ts`      | Lo que se anota de cada ejecución.                                                             |
| `runner/worker/src/purge.ts`         | La limpieza diaria.                                                                            |
| `runner/worker/src/schema.sql`       | El esquema de la base D1.                                                                      |
| `tools/dashboard.py`                 | El panel del operador: lee D1 y muestra dónde se atascan los alumnos.                          |
| `runner/worker/src/http.ts`          | Las respuestas y la comprobación de origen que comparten `/auth` y `/api`.                     |
| `runner/worker/src/contract.ts`      | La forma de un id de ejercicio.                                                                |
| `runner/worker/src/log.ts`           | Las únicas líneas que el Worker escribe en su registro.                                        |
| `runner/worker/test/`                | Las pruebas del Worker con un contenedor y un proveedor OAuth falsos.                          |
| `runner/worker/test/serve.ts`        | El mismo Worker en local, para las pruebas de navegador de la cuenta.                          |
| `site/account.js`                    | El cliente de la cuenta: el menú, la unión al cargar y el envío al escribir.                   |
| `site/privacidad.html`               | La página de privacidad.                                                                       |
| [`deploy.md`](deploy.md)             | Los pasos para publicar una copia propia.                                                      |
| `exercises/<lección>/<ejercicio>/`   | La imagen solo lleva `check.py` de cada uno.                                                   |

## Ejecutarlo con Docker

```sh
python runner/local.py serve
```

Construye la imagen `qg-runner` si hace falta (`python runner/local.py build`),
la arranca y escribe su URL. Usa gVisor (`runsc`) si Docker lo tiene registrado
y `runc` si no; `--runtime` lo fuerza. El contenedor va en una red interna de
Docker, sin salida a internet, con el sistema de archivos de solo lectura y sin
más capacidades que `SETUID`, `SETGID`, `KILL`, `CHOWN`, `FOWNER`,
`DAC_OVERRIDE` y `SYS_PTRACE` (el corredor la usa para leer la memoria de los
procesos del alumno). Se alcanza por su IP, lo que funciona en Linux.

```sh
curl -s $URL/run -d '{"code": "print(2 + 2)"}'
```

## Pruebas y medidas

```sh
mise run test:integration
python runner/bench.py --runs 50
```

`tests/runner_test.py` construye la imagen, la arranca y habla con `/run` por
HTTP. Cubre el contrato, que el resultado de cada ejercicio sea el de
`qgcheck.grade`, los intentos de falsear un resultado y cada límite. Se salta si
Docker no responde.

```sh
mise run test:worker
```

Las pruebas del Worker (`runner/worker/test/`) arrancan el Worker real en el
runtime local de Cloudflare (Miniflare), con `site/` como archivos estáticos y
las mismas rutas de entrada que el despliegue, y con un contenedor falso que
anota cada llamada, una base D1 local y un proveedor OAuth falso que hace de
Google y de GitHub. No necesitan Docker ni cuenta. Comprueban que `GET /` sirve
`index.html`, que `POST /run` devuelve el JSON del corredor y cada límite de
[Protección del Worker](#protección-del-worker) por su respuesta y, con el
contenedor falso, que una petición rechazada no lo alcanza. También recorren el
inicio de sesión, los [endpoints de la cuenta](#cuentas), lo que se guarda de
cada ejecución y la limpieza diaria. Dos pruebas llaman al `siteverify` real con
las claves de prueba y se saltan si no hay red.

`tests/account_ui_test.py` arranca `runner/worker/test/serve.ts`, que sirve ese
mismo Worker en local con el proveedor falso, y lo recorre con un navegador:
termina una lección y falla una comprobación sin cuenta, entra, abre otro
navegador con la misma cuenta, borra la cuenta y mira qué queda en el servidor y
en el navegador. Se ejecuta dentro de `mise run test:ui`.

## Cloudflare Containers

`runner/worker/` es un solo Worker, `qiskit-guides`, que sirve el sitio, el
corredor y las cuentas en el mismo origen: el editor llama a `/run` y la cookie
de sesión de Turnstile es `SameSite=Strict`.

- Los archivos de `site/` son sus archivos estáticos. El directorio lo fija
  [`wrangler.config.ts`](../runner/worker/wrangler.config.ts).
- `/run`, `/health`, `/auth/*` y `/api/*` entran al código del Worker antes que
  a los archivos (`run_worker_first`). La lista está en
  [`src/routes.ts`](../runner/worker/src/routes.ts), que usan también el
  despliegue y las pruebas. Cualquier otra ruta la responde el servicio de
  archivos sin ejecutar el Worker, y una ruta que no es un archivo responde 404.
  Una ruta de `/auth/*` o de `/api/*` que no existe la responde el Worker con
  404 y `reason` `not_found`.
- Una clase `Runner` que extiende `Container` (`@cloudflare/containers`) reparte
  las peticiones de `/run` entre dos instancias. Si la instancia elegida
  responde 503, repite la petición una vez en la otra. La instancia no tiene
  salida a internet (`enableInternet = false`) y se apaga a los 60 segundos sin
  peticiones.

Un solo `cf deploy` construye la imagen, empaqueta el Worker y sube `site/` como
una versión. Para publicar un cambio de las lecciones hay que volver a
desplegar.

### Lo que fija el operador

El plan Workers Paid, Docker, la base D1, el widget de Turnstile y los clientes
OAuth son de la cuenta de quien despliega. [deploy.md](deploy.md) da los pasos.
Los valores y los secretos que el Worker lee están en
[Variables y secretos](#variables-y-secretos). El Worker no declara `domains`:
sale en `<nombre>.<subdominio>.workers.dev`.

## Cuentas

Una cuenta es opcional. Sin ella todo funciona y el progreso se queda en el
navegador (`localStorage`). Con ella el progreso se guarda en una base D1 y se
comparte entre dispositivos. Se entra con Google o con GitHub, sin contraseña.

| Método y ruta                      | Qué hace                                                                     |
| ---------------------------------- | ---------------------------------------------------------------------------- |
| `GET /auth/google`, `/auth/github` | Redirige al proveedor. `?return=/ruta` dice adónde volver (por defecto `/`). |
| `GET /auth/<proveedor>/callback`   | La vuelta del proveedor. Abre la sesión y redirige a `return`.               |
| `POST /auth/logout`                | Cierra la sesión. Responde 204.                                              |
| `GET /api/me`                      | Quién entró y su progreso.                                                   |
| `POST /api/merge`                  | Junta el progreso del navegador con el de la cuenta.                         |
| `PUT /api/progress`                | Guarda cambios de progreso. Responde 204.                                    |
| `DELETE /api/me`                   | Borra la cuenta y todo lo suyo.                                              |

Las respuestas de error llevan `{"error": "...", "reason": "..."}`. Los métodos
que cambian datos (`POST`, `PUT`, `DELETE`) exigen la cabecera `Origin` del
mismo origen y responden 403 `bad_origin` si no. Sin sesión, todo `/api` salvo
`GET /api/me` responde 401 `signed_out`. Una ruta que no existe responde 404
`not_found`, y un método equivocado, 405 `method` con `Allow`.

### Entrar

El inicio de sesión es el flujo de código de autorización de OAuth 2.0 con
`state` y PKCE (S256), escrito sin biblioteca en
[`src/auth.ts`](../runner/worker/src/auth.ts).

1. `GET /auth/<proveedor>` guarda un `state` al azar, el verificador PKCE y el
   `return` en la cookie `qg_oauth`
   (`Path=/auth; HttpOnly; Secure; SameSite=Lax`, 10 minutos) y redirige al
   proveedor. Google recibe el permiso `openid`; GitHub, ninguno. `return` solo
   puede ser una ruta de este sitio (empieza por una `/` y no por `//` ni `/\`,
   sin caracteres de control, hasta 200 caracteres); otra cosa responde 400
   `bad_return`. La redirección escribe en porcentaje (UTF-8) los caracteres que
   no son ASCII. Sin las credenciales del proveedor responde 503
   `provider_unavailable`.
2. La vuelta cambia el código por un token en el extremo del proveedor y lee de
   su extremo de datos solo el identificador: `sub` en Google, `id` en GitHub.
   Las peticiones a GitHub llevan `User-Agent: qiskit-guides`.
3. Si el identificador ya tiene usuario, entra en él; si no, se crea uno. Una
   sesión nueva sale en la cookie `qg_auth`
   (`Path=/; HttpOnly; Secure; SameSite=Lax`, `AUTH_SESSION_DAYS` días) y la
   respuesta redirige a `return`. La cookie `qg_oauth` se gasta en toda vuelta.

La vuelta se rechaza con 400 si falta la cookie `qg_oauth` o es de otro
proveedor (`flow_missing`), si el `state` no es el guardado (`state_mismatch`),
si no trae `code` (`code_missing`) o si el proveedor no acepta el código
(`code_rejected`: un código solo vale una vez). Si el proveedor no responde, 502
`provider_failed`. Si el alumno cancela en la pantalla del proveedor, la
respuesta redirige a `return` sin sesión.

Un proveedor y un identificador son una identidad. Ni dos proveedores ni dos
cuentas de un mismo proveedor se juntan: cada identidad nueva es un usuario
nuevo.

### El progreso

`GET /api/me` responde `{"signedIn": false}` sin sesión. Con ella:

```json
{
  "signedIn": true,
  "providers": ["google"],
  "progress": {
    "done": ["p1-quickstart"],
    "exercises": {
      "p1-quickstart/ghz": {
        "code": "…",
        "hints": 1,
        "checks": 3,
        "passed": true,
        "at": 1760000000000
      }
    },
    "kv": { "qiskit:hitos": [1, 3] }
  }
}
```

`done` son las lecciones terminadas. `exercises` guarda por ejercicio el código
(solo si la página lo manda), las pistas y las comprobaciones, si pasó y `at`,
los milisegundos Unix de la última edición. `kv` guarda las claves de
`localStorage` que siguen una de estas formas:

| Clave                                    | Valor              | Al juntar dos valores                                                 |
| ---------------------------------------- | ------------------ | --------------------------------------------------------------------- |
| `qiskit:heard:<lección>`, `qiskit:hitos` | lista de enteros   | la unión                                                              |
| `qiskit:misiones`                        | lista de textos    | la unión                                                              |
| `qiskit:pos:<lección>`                   | entero             | el mayor                                                              |
| `qiskit:predict:<lección>:<id>`          | entero             | el que ya estaba: una apuesta no cambia                               |
| `qiskit:repaso`                          | `{id: {box, due}}` | por pregunta, la caja mayor y, a igual caja, la fecha que vence antes |

`POST /api/merge` y `PUT /api/progress` reciben el mismo cuerpo (`done`,
`exercises` y `kv`, todos opcionales) y lo juntan con lo guardado:

- `done` se une.
- Por ejercicio, `hints` y `checks` son el mayor, `passed` es verdadero si lo
  era alguno, y el código es el de la edición con `at` mayor. Un código ausente
  o `null` no borra el guardado.
- `kv` se junta según la tabla.

Ninguna regla depende del orden, así que dos dispositivos que se sincronizan
acaban en el mismo estado. `POST /api/merge` responde `{"progress": {...}}` con
el resultado; `PUT /api/progress` responde 204. Una clave de `kv` o un campo que
el Worker no conoce responde 400 `bad_request`, para que un error de la página
se vea. El cuerpo es `application/json` (415 `content_type` si no) y de hasta
800 000 bytes (413 `too_large`). Una cuenta admite 500 lecciones, 100 ejercicios
y 2000 claves; pasarse responde 413 `too_much`. El código de un ejercicio mide
hasta 20 000 bytes. Dos escrituras a la vez del mismo usuario no se pisan: una
que encuentra el progreso cambiado vuelve a leer y a juntar. Si pierde 10 veces
seguidas responde 503 `busy` con `Retry-After`. El detalle está en
[architecture.md](architecture.md#runner).

`DELETE /api/me` borra el usuario y, por las claves foráneas, sus identidades,
sesiones, progreso e intentos. Responde `{"deleted": true}` y borra la cookie.

Cada endpoint de `/auth` cuenta contra un límite por IP, `AUTH_PER_MINUTE` por
minuto y `RATE_PER_DAY` por día, y responde 429 `rate_auth` al pasarse. Cada
endpoint de `/api` cuenta contra el límite por usuario de
[Límite por IP](#límite-por-ip).

### En el sitio

[`site/account.js`](../site/account.js) es el cliente. Pone el menú _Entrar_ en
la cabecera de la portada, de las lecciones y de
[`privacidad.html`](../site/privacidad.html), la página que dice qué se guarda,
cuánto tiempo y cómo borrarlo.

- Sin cuenta, la página no hace ninguna petición salvo `/run`. Lo que mira para
  saberlo es la marca `qiskit:cuenta` de `localStorage`.
- _Entrar con Google_ y _Entrar con GitHub_ van a `/auth/<proveedor>` con
  `return` igual a la página actual más `#cuenta`. Al volver, ese `#cuenta` hace
  que la página deje la marca y junte el progreso.
- Con la marca, cada carga manda todo el progreso del navegador a
  `POST /api/merge` y guarda la respuesta antes de que la página lo lea. Espera
  4 segundos como mucho; si el Worker no responde, la página sigue con lo local.
  La primera vez que entras, esa misma llamada junta lo que ya había en el
  navegador con lo de la cuenta.
- Cada cambio se manda después, en `PUT /api/progress`, 1,5 segundos después del
  último y siempre al cerrar o ocultar la página. Sin red, el cambio queda en
  `localStorage` y la siguiente carga lo junta.
- Cada `qiskit:exercise:<id>` lleva `at`, la hora de la última edición del
  código. Solo cambia al cambiar el código, no con las pistas ni las
  comprobaciones. Así gana la copia más reciente al juntar.
- Se sincronizan las lecciones hechas, el código, las pistas y las
  comprobaciones de cada ejercicio y las claves de `kv` de la tabla de arriba.
  El texto de las reflexiones (`qiskit:reflect`) no sale del navegador. Un valor
  que el Worker rechazaría (un código de más de 20 000 bytes, por ejemplo) se
  omite del cuerpo, porque rechazaría todo el cuerpo.
- _Cerrar sesión_ llama a `POST /auth/logout` y _Borrar mi cuenta_, tras una
  confirmación, a `DELETE /api/me`. Ninguna de las dos toca lo que hay en el
  navegador. Una respuesta 401 quita la marca.

El progreso local pasa a la cuenta con la que se entra, sea cual sea. En un
equipo compartido, quien entra después junta lo que dejó quien usó el navegador
antes.

### Datos que se guardan

El Worker no guarda correo, nombre, avatar ni contraseña: no los pide al
proveedor y descarta lo que este devuelve. El esquema es
[`src/schema.sql`](../runner/worker/src/schema.sql).

| Tabla            | Qué guarda                                                             |
| ---------------- | ---------------------------------------------------------------------- |
| `users`          | Un id al azar, el día de alta y el día de la última visita.            |
| `identities`     | Proveedor e identificador del proveedor de cada usuario.               |
| `sessions`       | El hash SHA-256 del token de `qg_auth` y su caducidad. Nunca el token. |
| `lesson_done`    | Las lecciones terminadas y cuándo.                                     |
| `exercise_state` | El código, las pistas, las comprobaciones y si pasó, por ejercicio.    |
| `kv`             | Las claves de `localStorage` de la tabla de arriba.                    |
| `attempts`       | Una fila por ejecución, con o sin cuenta.                              |

Cada respuesta 200 de `/run` escribe una fila en `attempts`, a partir del JSON
que devolvió el contenedor, que es quien califica el código. La fila lleva el
momento, el `user_id` (`NULL` sin cuenta), el ejercicio, el modo, el resultado
(`pass`, `fail`, `error` o `timeout`), los nombres de los casos que fallaron, el
nombre de la excepción de Python (o `other`, o `killed_memory`, `killed_disk`,
`killed_output` o `killed_scan`), las pistas que la página dice haber usado
(cabecera `X-Hints`, un dígito del 0 al 9), `ms` y el tamaño del código en
bytes. No lleva el código, `stdout`, el texto del error ni el `message` de un
caso, que pueden repetir lo que escribió el alumno. Solo se anota una ejecución
con `mode` `run` o `check` y un `exercise` con la forma de un valor del
contrato. Un fallo al escribir la fila se registra y la respuesta no cambia.

### Retención

| Variable                 | Valor | Qué se borra                                        |
| ------------------------ | ----- | --------------------------------------------------- |
| `ATTEMPT_RETENTION_DAYS` | 180   | Los intentos de más de esos días.                   |
| `ACCOUNT_RETENTION_DAYS` | 730   | Las cuentas sin una visita en esos días (24 meses). |

Un cron diario (`17 3 * * *`, UTC) llama al manejador `scheduled` del Worker,
que borra en un solo lote los intentos vencidos, las sesiones caducadas y las
cuentas inactivas. Borrar una cuenta arrastra todo lo suyo. Una visita es una
petición con sesión de cuenta, y se anota a lo sumo una vez al día.

### Dónde se atascan los alumnos

`tools/dashboard.py` lee la base con `wrangler d1 execute` y no escribe nada.
`uv run python tools/dashboard.py --database-id <uuid>` lee la base remota, con
la sesión de `bunx wrangler login` (en `runner/worker`) o
`CLOUDFLARE_API_TOKEN`, y `--local` lee la copia local de `--persist-to`.
Imprime, para el periodo de `--since` a `--until` (días UTC, por defecto los
últimos 30), los usuarios nuevos, los que intentaron algo y los intentos con y
sin cuenta; las lecciones terminadas por lección; los ejercicios con más
comprobaciones fallidas y los casos que más fallan; y los ejercicios aprobados
con más pistas abiertas. Una comprobación fallida es un intento `check` que no
acabó en `pass`, y cuenta también sin cuenta. Las lecciones terminadas y las
pistas salen de las tablas de una cuenta, así que no cuentan a nadie anónimo.
`--json` imprime lo mismo como JSON y `--limit` fija las filas de cada ranking
(10 por defecto).

### Variables y secretos

Los secretos se crean con `bindings.secret()` en
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts) y no se escriben
en el repositorio. [deploy.md](deploy.md) dice dónde se obtiene cada uno y cómo
se guarda.

| Nombre                                     | Tipo    | Para qué                                                          |
| ------------------------------------------ | ------- | ----------------------------------------------------------------- |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | secreto | El cliente OAuth de Google.                                       |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | secreto | La aplicación OAuth de GitHub.                                    |
| `TURNSTILE_SECRET`                         | secreto | El widget de Turnstile; también clave del HMAC de los contadores. |
| `DB`                                       | D1      | La base de datos.                                                 |
| `AUTH_PER_MINUTE`                          | 10      | Peticiones por IP y minuto a `/auth/*`.                           |
| `AUTH_SESSION_DAYS`                        | 30      | Duración de la cookie `qg_auth`.                                  |
| `SIGNED_IN_IP_FACTOR`                      | 4       | Cuánto sube el tope por IP de quien tiene cuenta.                 |
| `ATTEMPT_RETENTION_DAYS`                   | 180     | Ver [Retención](#retención).                                      |
| `ACCOUNT_RETENTION_DAYS`                   | 730     | Ver [Retención](#retención).                                      |

El Worker arma el `redirect_uri` con el origen de la petición. Qué registrar en
cada proveedor lo dice [deploy.md](deploy.md).

## Protección del Worker

El Worker comprueba cada `POST /run` antes de arrancar el contenedor. Las
comprobaciones van en este orden, y la primera que falla responde sin que el
contenedor reciba nada:

1. El límite por IP.
2. El límite por usuario, si la petición trae una sesión de cuenta (`qg_auth`)
   que no es de un mantenedor.
3. El tamaño del cuerpo y del código.
4. El presupuesto del mes y del día ([Presupuesto](#presupuesto)).
5. Turnstile, si la petición no es de un mantenedor ni trae una sesión de
   Turnstile válida.

Una negativa lleva `{"error": "...", "reason": "..."}`. El editor muestra el
texto de `error` tal cual. Todos los valores salen de `env` en
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts); cambiarlos es
editar ese archivo y desplegar. Un valor ausente o que no es un número positivo
hace que el Worker responda 500 con `internal_error` y registre qué variable
falló.

`GET /health` lo responde el Worker con 200 sin tocar un contenedor, para que
una petición sin límite no pueda mantener una instancia encendida.

### Límite por IP

| Variable          | Valor | Significa                                   |
| ----------------- | ----- | ------------------------------------------- |
| `RATE_PER_MINUTE` | 30    | Peticiones por IP en cada minuto del reloj. |
| `RATE_PER_DAY`    | 1000  | Peticiones por IP en cada día UTC.          |

Cuenta toda petición a `/run` desde que llega, también las que luego se rechazan
por tamaño o por Turnstile. Pasado el límite responde 429 con `Retry-After` en
segundos y `reason` `rate_minute` o `rate_day`. El alumno ve:

- «Estás ejecutando demasiado seguido. Espera 12 s y vuelve a intentarlo.»
- «Llegaste al límite de ejecuciones de hoy. Puedes volver a ejecutar en 5 h.»

La IP es `CF-Connecting-IP`. Sin esa cabecera (en local) todas las peticiones
comparten un solo contador. Una clase entera detrás de una misma IP comparte el
límite.

Con una sesión de cuenta, el tope por IP es `SIGNED_IN_IP_FACTOR` veces el
anónimo (4: 120 por minuto y 4000 por día) y el que acota a cada alumno es el
suyo, con los mismos valores de `RATE_PER_MINUTE` y `RATE_PER_DAY`. Así una
clase entera con cuenta cabe detrás de una IP, y un solo alumno no gasta más que
uno anónimo. La respuesta 429 es la misma, con `reason` `rate_minute` o
`rate_day`.

Cada contador vive en un Durable Object `RateLimiter` que se nombra con un HMAC
de la etiqueta (`limiter` para una IP, `user`, `auth` o `api`), del día y de la
clave (la IP o el id del usuario). La clave del HMAC sale de `TURNSTILE_SECRET`,
así que el nombre no se puede volver a una IP ni a un usuario sin ese secreto.
El objeto guarda dos contadores y borra su estado cuando termina el día.

### Tamaño del código

| Variable         | Valor  | Significa                     |
| ---------------- | ------ | ----------------------------- |
| `MAX_CODE_BYTES` | 20 000 | Bytes UTF-8 del campo `code`. |

Un código mayor responde 413 con `reason` `too_large` y el alumno ve «El código
ocupa 20001 bytes y el máximo son 20000.». Un cuerpo mayor que seis veces el
máximo más 1024 bytes responde 413 sin leerse entero. Un cuerpo que no es JSON o
no trae `code` como texto responde 400 (`bad_request`). El contenedor repite la
comprobación con `MAX_CODE` de `qgcheck/runner.py`; para cambiar el tope hay que
cambiar los dos.

### Presupuesto

Cloudflare no tiene un tope de gasto: sus alertas de presupuesto solo mandan un
correo ([deploy.md](deploy.md#10-pon-alertas-de-gasto)). Por eso el Worker
cuenta lo que gasta y se niega a ejecutar cuando el gasto estimado del mes
llegaría a `MONTHLY_BUDGET_USD`. La cuenta es una cota superior de lo que
factura Cloudflare Containers. No incluye los 5 USD al mes del plan Workers
Paid, que se pagan aparte.

| Variable                | Valor      | Significa                                                           |
| ----------------------- | ---------- | ------------------------------------------------------------------- |
| `MONTHLY_BUDGET_USD`    | 2          | Gasto estimado del mes UTC que no se supera.                        |
| `PUBLIC_BUDGET_SHARE`   | 0.75       | Parte del presupuesto que gasta quien no mantiene el sitio.         |
| `PUBLIC_BUDGET_DAYS`    | 15         | Un día de gasto público no pasa de 1/15 de esa parte.               |
| `INSTANCE_TYPE`         | standard-2 | Tipo de instancia. De él salen los precios.                         |
| `INSTANCES`             | 2          | Instancias entre las que el Worker reparte las ejecuciones.         |
| `RESERVED_BUSY_SECONDS` | 30         | Segundos que una ejecución aparta del presupuesto antes de empezar. |
| `MAINTAINERS`           | ids        | Ver [Mantenedores](#mantenedores).                                  |

`INSTANCE_TYPE` e `INSTANCES` se declaran una vez en
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts), que los usa
para la instancia que despliega y para el Worker. No hay un precio que editar:
[`src/container.ts`](../runner/worker/src/container.ts) tiene la tarifa de
Cloudflare y las medidas de cada tipo, y de ahí sale el precio del segundo de
CPU y el del segundo de instancia encendida.

#### Qué cuesta una ejecución

Cloudflare factura la CPU solo mientras la instancia trabaja, y la memoria y el
disco durante todo el tiempo que está encendida, trabaje o no. La instancia se
apaga `sleepAfter` (60 s) después de su última petición. Con `standard-2` (1
vCPU, 6 GiB y 12 GB) un segundo cuesta:

| Concepto             | Cuenta                          | USD por segundo |
| -------------------- | ------------------------------- | --------------- |
| CPU, solo trabajando | 1 × 0,00002                     | 0,00002         |
| Encendida, siempre   | 6 × 0,0000025 + 12 × 0,00000007 | 0,00001584      |

El Worker aparta y cobra así, en el Durable Object `Budget`, que guarda por
instancia el instante en que se espera que se apague (`awakeUntil`):

1. Antes de arrancar el contenedor aparta la ejecución más cara que cabe en
   `RESERVED_BUSY_SECONDS`: esos segundos de CPU y los segundos encendida desde
   `max(ahora, awakeUntil)` hasta `ahora + RESERVED_BUSY_SECONDS + sleepAfter`.
   Una instancia que ya estaba encendida solo cobra lo que la ejecución alarga
   su ventana. Los segundos se cobran en pasos de 10 ms.
2. Si la reserva no cabe, no ejecuta ([Qué se rechaza](#qué-se-rechaza)).
   Comprobar y apartar es una sola operación del objeto, así que varias
   peticiones simultáneas no pueden apartar a la vez lo que solo cabe una vez.
3. Al terminar cambia la reserva por el coste medido: el tiempo que esperó al
   contenedor (el arranque incluido) a la tarifa de CPU y la ventana encendida
   hasta `sleepAfter` después de que respondió, y nunca más de lo apartado. Solo
   la reserva que fijó `awakeUntil` lo acorta; si otra lo alargó después, esa
   parte sigue cobrada, porque esa otra cobró desde donde esta acababa.
4. Una petición que se rechaza después de apartar (por Turnstile) devuelve la
   reserva entera. El total del mes y el del día anteriores se descartan.

`RESERVED_BUSY_SECONDS` es un tope y no una estimación. Cubre los 10 s de
trabajo de [Límites](#límites), el arranque de una instancia y el reintento tras
un 503. Si la ejecución, con su reintento, llega a ese tiempo, el Worker detiene
la instancia que aún no había respondido, cobra lo apartado y responde 504 con
`reason` `run_too_long`. Una instancia que respondió 503 atiende el trabajo de
otro alumno y no se detiene. El reintento aparta su propia reserva en la
instancia siguiente. El alumno ve «La ejecución tardó más de lo que el corredor
permite y se detuvo. Revisa si el código tiene un bucle sin fin.» Como cada
ejecución cuesta como mucho lo que apartó y solo se aparta si cabe, el gasto
estimado no pasa del presupuesto. Si el Worker se interrumpe entre apartar y
terminar, o falla el almacenamiento al terminar (se registra con
`where: "settle"` y la respuesta no cambia), la reserva se queda y el mes cuenta
de más, nunca de menos.

#### Un ejemplo con `standard-2`

Cifras que salen de las tarifas anteriores, con `RESERVED_BUSY_SECONDS` de 30:

- **Una ejecución aislada de 2 s**, sin otra en los 60 s anteriores: 2 × 0,00002
  de CPU más 62 s encendida (2 s de trabajo y 60 de espera) × 0,00001584. Son
  0,00102 USD. Una de 1 s cuesta 0,00099 USD y una de 10 s, 0,00131 USD: casi
  todo es la espera, no el trabajo. Antes de empezar aparta 0,0020256 USD.
- **100 ejecuciones de 1 s en un minuto**, repartidas entre las dos instancias y
  seguidas (50 s de trabajo cada una): 100 × 0,00002 de CPU más 2 instancias
  encendidas 110 s (50 de trabajo y 60 de espera) × 0,00001584. Son 0,0055 USD,
  menos de lo que cuestan 6 ejecuciones aisladas, porque las ejecuciones que
  llegan con la instancia encendida solo alargan su ventana. Las mismas 100
  ejecuciones, cada una con más de 60 s de diferencia de la anterior, cuestan
  0,099 USD.
- **Cuántas ejecuciones aisladas de 2 s caben en 2 USD**: 1955 en total. Quien
  no mantiene el sitio dispone de 1,5 USD, que son 1466; los 0,5 USD restantes
  son de los mantenedores. En un día el gasto público no pasa de 0,10 USD (1,5
  USD entre 15), que son 96 ejecuciones aisladas.

#### Qué se rechaza

| Quién      | Tope                                     | `reason`     |
| ---------- | ---------------------------------------- | ------------ |
| Público    | 75 % del presupuesto, gastado por todos  | `budget`     |
| Público    | 1/15 de ese 75 %, gastado en el día UTC  | `budget_day` |
| Mantenedor | El presupuesto entero, gastado por todos | `budget`     |

Un mantenedor no tiene tope diario, y lo que gasta cuenta en el 75 % del
público. Todas las negativas son 503 con `Retry-After` en segundos. `budget`
espera al día 1 del mes siguiente y `budget_day` a la medianoche UTC. El alumno
ve:

- `budget`: «El corredor alcanzó su presupuesto de este mes y no ejecuta más
  código hasta que empiece el siguiente. Los cuadernos de marimo siguen
  funcionando en tu equipo.»
- `budget_day`: «El corredor alcanzó su presupuesto de hoy y no ejecuta más
  código hasta mañana. Puedes volver a ejecutar en 5 h. Los cuadernos de marimo
  siguen funcionando en tu equipo.»

#### Mantenedores

`MAINTAINERS` es una lista de ids numéricos de GitHub separados por comas, sin
logins: un login se puede renombrar y otra persona puede quedárselo, y el id no
cambia. Quien entró con GitHub y tiene su id en la lista es mantenedor. No pasa
por Turnstile, no tiene el límite por usuario de [Límite por IP](#límite-por-ip)
y gasta del presupuesto entero. El límite por IP y el tamaño del código siguen
valiendo para él. Una cuenta de Google nunca es mantenedora, aunque su
identificador sea el mismo número. Un valor que no sea una lista de ids hace que
el Worker responda 500 y registre `MAINTAINERS`.
[deploy.md](deploy.md#9-elige-los-mantenedores) dice cómo ver el id de una
cuenta.

#### Lo que la estimación no cuenta

La cuenta es una cota superior: ignora las cuotas mensuales incluidas en Workers
Paid, y cobra la CPU de todo el tiempo que la petición esperó al contenedor, el
arranque incluido, aunque Cloudflare solo la factura mientras trabaja. Lo que
puede quedar fuera:

- Una instancia que el Worker no logra detener al llegar al tope (se registra
  con `where: "stop"`). Cloudflare la factura hasta que se apague sola.
- Una instancia que sigue arrancando cuando se llega al tope no ha respondido
  aún, así que el Worker la detiene aunque otro alumno haya llegado a ella
  durante el arranque.

La suma de `cost_nano_usd` en el registro da el gasto estimado del mes.

### Turnstile

Cloudflare Turnstile se verifica en la primera ejecución de cada sesión, con
cuenta o sin ella. Solo un [mantenedor](#mantenedores) no pasa por Turnstile: la
petición ni llama a `siteverify` ni recibe `qg_session`. Una petición sin sesión
de Turnstile y sin token recibe 403 `turnstile_missing` con la clave del sitio
en el campo `sitekey`. Con ella, `site/exercise.js` carga el widget, y repite la
petición con el token del widget en la cabecera `X-Turnstile-Token`. El Worker
lo comprueba con `siteverify`, al que envía solo el secreto y el token, y si
vale responde con la cookie `qg_session` además del resultado:

```text
qg_session=<caducidad>.<mac>; Max-Age=28800; Path=/run; HttpOnly; Secure; SameSite=Strict
```

La cookie lleva la hora de caducidad y un MAC que cubre esa hora y la IP. No
lleva ningún identificador, y no sirve desde otra IP ni pasada su caducidad. Las
siguientes ejecuciones la mandan solas y no vuelven a llamar a Turnstile.

| Respuesta | `reason`                | El alumno ve                                                                                           |
| --------- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| 403       | `turnstile_missing`     | «Antes de ejecutar código hay que comprobar que eres una persona.»                                     |
| 403       | `turnstile_failed`      | «No pasó la comprobación de que eres una persona. Recarga la página e inténtalo de nuevo.»             |
| 503       | `turnstile_unavailable` | «No se pudo comprobar que eres una persona. Vuelve a intentarlo en unos segundos.» (`Retry-After: 10`) |

| Variable             | Valor         | Significa                                                          |
| -------------------- | ------------- | ------------------------------------------------------------------ |
| `SESSION_HOURS`      | 8             | Duración de la sesión verificada.                                  |
| `TURNSTILE_SITE_KEY` | configuración | La clave pública del widget configurada en `cloudflare.config.ts`. |

`TURNSTILE_SECRET` es un secreto del Worker (`bindings.secret()`), no un valor
del repositorio. La clave del sitio no es secreta: el Worker se la da a la
página en la respuesta `turnstile_missing`. Con `TURNSTILE_SITE_KEY` vacía, un
`POST /run` anónimo responde 500 `internal_error` y registra la variable que
falta. Cloudflare documenta claves de prueba que no necesitan cuenta:

| Clave                                 | Tipo    | Comportamiento                                                |
| ------------------------------------- | ------- | ------------------------------------------------------------- |
| `1x00000000000000000000AA`            | sitio   | Siempre pasa. El token que genera es `XXXX.DUMMY.TOKEN.XXXX`. |
| `1x0000000000000000000000000000000AA` | secreto | Siempre pasa.                                                 |
| `2x0000000000000000000000000000000AA` | secreto | Siempre falla.                                                |
| `3x0000000000000000000000000000000AA` | secreto | Responde que el token ya se usó.                              |

Las pruebas del Worker usan los tres secretos.

### Qué recibe el contenedor y qué se registra

El contenedor recibe el cuerpo de la petición y `Content-Type`. No recibe la
cookie, el token ni la IP.

El Worker escribe estos registros y ningún otro. Todos tienen campos fijos, que
`src/log.ts` define.

1. Una línea `run` por cada petición a `/run` que el Worker contesta, con
   cualquier resultado menos un error interno:

   ```json
   {
     "event": "run",
     "outcome": "ok",
     "status": 200,
     "mode": "check",
     "exercise": "p1-quickstart/ghz",
     "code_bytes": 212,
     "busy_ms": 930,
     "cost_nano_usd": 983732
   }
   ```

   `outcome` es `ok`, `rate_minute`, `rate_day`, `bad_request`, `too_large`,
   `budget`, `budget_day`, `turnstile_missing`, `turnstile_failed`,
   `turnstile_unavailable` o `run_too_long`. `mode` y `exercise` se copian solo
   si tienen la forma de un valor del contrato.

2. Una línea de error, en lugar de la anterior, cuando la petición falla por un
   error del Worker o de la configuración y responde 500 `internal_error`:

   ```json
   {
     "event": "run",
     "outcome": "internal_error",
     "status": 500,
     "error": "Error"
   }
   ```

   `error` es el nombre de la clase del error. `detail` lleva el texto solo si
   es un error de configuración, que nombra una variable y no datos.

3. Una línea de error aparte, además de la línea de la propia petición, cuando
   un paso posterior falla y la petición sigue su camino. Lleva `where` y no
   lleva `status`:
   - `"settle"`: falló el ajuste del presupuesto.
   - `"stop"`: falló detener una instancia al llegar al tope de la reserva.
   - `"attempt"`: falló anotar el intento en la base. La respuesta no cambia.

4. Una línea de error con `event` `auth`, `api` o `purge` cuando falla un
   endpoint de [Cuentas](#cuentas) o la limpieza diaria. Lleva `outcome`
   `internal_error`, `status` 500 y `error` con el nombre de la clase. Un
   endpoint responde 500 `internal_error`; la limpieza deja que falle el cron.

Ningún registro lleva el código, la IP, el token, la cookie ni el texto de un
error. `cloudflare.config.ts` activa Workers Logs con el registro de
invocaciones apagado, que es el que lleva la petición. Lo que Cloudflare guarda
de su red no depende del Worker.

### Por qué estos valores

Los valores salen de las tarifas de Containers con la instancia `standard-2` y
de dos instancias que atienden un trabajo cada una (las cifras de
[Presupuesto](#presupuesto)):

- Dos instancias encendidas todo el mes costarían unos 82 USD (2 × 0,00001584 ×
  2 592 000 s). Con `sleepAfter` de 60 s y el tope de 2 USD, el Worker no puede
  dejar que eso ocurra: cada segundo encendido se cuenta.
- 30 por minuto es una ejecución cada 2 s. Con ejecuciones de 1 s una IP ocupa
  30 s de los 120 s de instancia que hay cada minuto.
- 1000 por día, todas de 1 s y aisladas, costarían a una IP 0,99 USD. El tope
  diario público (0,10 USD) la para antes.
- Un atacante con muchas IPs gasta como mucho 0,10 USD al día, que son 96
  ejecuciones aisladas de 2 s, así que la parte pública del mes le dura al menos
  15 días. Los mantenedores conservan el último 25 %.

Son cálculos con esas tarifas, no medidas del Worker desplegado.
