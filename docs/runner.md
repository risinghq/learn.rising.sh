# El corredor de código

El corredor ejecuta el código de un alumno con Qiskit y Qiskit Aer y devuelve lo
que imprimió y el resultado de los casos de un ejercicio, con el formato de
[`qgcheck.grade`](exercises.md#corregir-código). Es una imagen de contenedor con
un servidor HTTP y el mismo contrato en Cloudflare Containers y en Docker. El
editor de las lecciones lo llama con `POST /run`. Lo que el Worker comprueba
antes de llamarlo está en [protection.md](protection.md). En tu equipo,
`tools/serve.py` responde `/run` sin aislamiento.

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
  ([exercises.md](exercises.md#escribir-checkpy)).
- `killed` es `time`, `memory`, `disk` u `output` cuando el corredor mató el
  trabajo por ese límite, y `null` si no. Es `scan` si falló la lectura de
  memoria o disco que vigila los límites: sin poder medir, el corredor mata el
  trabajo en vez de dejarlo correr sin tope.
- `ms` es el tiempo del trabajo dentro del corredor. `peak_mb` es la mayor suma
  de la memoria proporcional (PSS) de los procesos del trabajo.

Otras respuestas llevan `{"error": "..."}`: 400 si la petición no es válida, 404
si el ejercicio no existe, 413 si el código pasa de 20 000 bytes o el cuerpo de
121 024 (seis veces el código, que es lo que ocupa un carácter de control en
JSON, más 1024 de envoltura) y 503 si no queda una ranura libre. `GET /health`
responde 200.

## Límites

| Límite                | Valor          | Cómo se aplica                                                                                                                                      |
| --------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tiempo                | 10 s           | `sandbox.py` mata el grupo de procesos y todo proceso del mismo uid.                                                                                |
| Memoria               | 512 MB         | `sandbox.py` mide cada 20 ms y mata si la memoria proporcional (PSS) pasa. `RLIMIT_DATA` hace fallar antes una asignación grande con `MemoryError`. |
| Directorio de trabajo | 64 MB          | `sandbox.py` mide cada 100 ms. Más de 5000 entradas cuentan como disco lleno.                                                                       |
| Un archivo            | 16 MB          | `RLIMIT_FSIZE`.                                                                                                                                     |
| Procesos e hilos      | 64             | `RLIMIT_NPROC` sobre el uid de la ranura.                                                                                                           |
| Salida                | 64 KiB         | `sandbox.py` mata el trabajo al pasarse.                                                                                                            |
| Tiempo de CPU         | tiempo + 2 s   | `RLIMIT_CPU`.                                                                                                                                       |
| Red                   | solo `AF_UNIX` | Un filtro seccomp de `launcher.py` niega `socket` de cualquier otra familia.                                                                        |
| Escritura             | su directorio  | Un uid sin privilegios. `/scratch`, `/tmp`, `/var/tmp` y `/app` son de root.                                                                        |

Los valores se cambian con `QG_WALL_S` (10), `QG_MEM_MB` (512) y `QG_SCRATCH_MB`
(64).

La memoria se mide leyendo el RSS cada 20 ms y el PSS cuando el RSS pasa del
tope y, en todo caso, cada 0,5 s. El PSS reparte una página compartida entre los
procesos que la usan, así que cuenta una vez.

## Ranuras

El servidor ejecuta tantos trabajos a la vez como ranuras tiene (`QG_JOBS`, por
defecto 1). La ranura `n` usa siempre el uid `20000 + n`. Un trabajo corre con
ese uid, sin capacidades y con `no_new_privs`.

Los números de las ranuras libres están en la cola `FREE_SLOTS` de `server.py`.
Una petición válida toma una ranura sin esperar: si no hay, responde 503. Solo
el hilo que la tomó la devuelve, y solo después de matar los procesos de ese uid
y de borrar su directorio y lo que dejó en `/scratch`, `/tmp`, `/var/tmp` y
`/dev/shm`. Ese borrado aísla un trabajo del anterior, porque el uid se
reutiliza. Las instancias de Cloudflare no comparten nada: cada una tiene sus
ranuras.

## El trabajo

El trabajo es `python -u -P -m qgcheck.job`, el mismo que lanza
[`qgcheck.grade`](exercises.md#corregir-código) en tu equipo sin los límites de
arriba. Con `mode: "run"` el código del alumno corre en ese proceso. Con
`mode: "check"` hay dos procesos del mismo uid:

- El comprobador (`qgcheck/job.py`) corre los casos de `check.py`. Antes de
  importar nada instala el filtro de importaciones diferidas de Python
  (`sys.set_lazy_imports_filter`) para `qiskit_ibm_runtime` y
  `qiskit_mitigation`: sus clientes y `scipy` se cargan al usarlos. Después se
  declara no volcable e importa las bibliotecas de `PRELOAD_ROOTS`
  (`qgcheck/source.py`) que usan el código del alumno y `check.py`.
- El proceso del alumno (`qgcheck/host.py`) es un `fork` del comprobador, hecho
  antes de importar `check.py`, así que hereda las bibliotecas ya cargadas y
  ningún valor esperado. Cierra los descriptores heredados salvo la entrada, la
  salida, el error y su extremo de un `socketpair` con el comprobador, ejecuta
  el código del alumno una vez y atiende las peticiones una a una en ese mismo
  proceso: el estado de nivel superior pasa de una a otra y su salida se muestra
  una vez. No bifurca por petición porque el código del alumno ya puede haber
  creado hilos (Qiskit los crea al transpilar) y el hijo de un proceso con hilos
  se bloquea.

Cada acceso a `learner.<nombre>` de un caso es una petición por el socket: qué
nombres hay, el valor de uno o su llamada. Los mensajes son JSON con la longitud
delante (`qgcheck/wire.py`, hasta 4 MiB) y llevan un `id` que el comprobador
sortea en cada petición. Solo viajan datos: números, textos, listas, tuplas,
diccionarios con claves de texto, `bytes`, arreglos de NumPy, `Statevector`,
`Operator`, `SparsePauliOp` y `QuantumCircuit` en QPY. Nunca se deserializa
código. Un caso que necesita pasar o recibir otra cosa la maneja en una función
de `check.py` marcada con `@inside`, que corre en el proceso del alumno y
devuelve datos ([exercises.md](exercises.md#escribir-checkpy)).

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

| Archivo              | Función                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| `runner/server.py`   | El servidor HTTP y la validación de la petición.                                               |
| `runner/sandbox.py`  | Lanza el trabajo y vigila tiempo, memoria, disco y salida.                                     |
| `runner/launcher.py` | Fija los rlimits, baja de uid e instala el filtro seccomp antes del `exec`.                    |
| `runner/Dockerfile`  | La imagen. Python y uv salen de `mise.toml`; las bibliotecas, del grupo `runner` de `uv.lock`. |
| `runner/local.py`    | Construye la imagen y la ejecuta con Docker y las banderas de aislamiento.                     |
| `runner/bench.py`    | Mide la latencia fría y templada.                                                              |
| `qgcheck/job.py`     | El trabajo: el comprobador de `check` y la ejecución de `run`.                                 |
| `qgcheck/host.py`    | El proceso del alumno de `check`.                                                              |
| `qgcheck/wire.py`    | El formato de mensajes entre esos dos procesos.                                                |
| `qgcheck/`           | El corrector de [exercises.md](exercises.md). La imagen lo copia sin cambios.                  |
| `exercises/*/*/`     | La imagen solo lleva el `check.py` de cada ejercicio.                                          |
| `runner/worker/`     | El Worker que sirve el sitio y arranca la imagen. [protection.md](protection.md)               |

## En Cloudflare

`runner/worker/` es un solo Worker, `duo`, que sirve el catálogo, los cursos, el
corredor y las cuentas en el mismo origen, `edu.rising.sh`: el editor llama a
`/run` y la cookie de sesión de Turnstile es `SameSite=Strict`.

- Los archivos de `site/` son sus archivos estáticos. El directorio lo fija
  [`wrangler.config.ts`](../runner/worker/wrangler.config.ts).
- `/run`, `/health`, `/auth/*` y `/api/*` entran al código del Worker antes que
  a los archivos (`run_worker_first`). La lista está en
  [`src/routes.ts`](../runner/worker/src/routes.ts), que usan también el
  despliegue y las pruebas. Un archivo del sitio lo responde el servicio de
  archivos sin ejecutar el Worker: `/` es el catálogo y `/qiskit/` el curso. Una
  ruta que no es un archivo pasa al Worker, que se la devuelve al servicio de
  archivos, y este responde 404. Una ruta de `/auth/*` o de `/api/*` que no
  existe la responde el Worker con 404 y `reason` `not_found`. Un `/run` que no
  es `POST` responde 405.
- Una clase `Runner` que extiende `Container` (`@cloudflare/containers`) reparte
  las peticiones de `/run` entre las dos instancias (`INSTANCES`). Si la elegida
  responde 503, repite la petición una vez en la siguiente. La instancia no
  tiene salida a internet (`enableInternet = false`) y se apaga a los 60 s sin
  peticiones.

Un solo `cf deploy` construye la imagen, empaqueta el Worker y sube `site/` como
una versión. Para publicar un cambio de las lecciones hay que volver a
desplegar: [deploy.md](deploy.md).

## Ejecutarlo con Docker

```sh
python runner/local.py serve
```

Construye la imagen `qg-runner` si hace falta (`python runner/local.py build`),
la arranca y escribe su URL. Usa gVisor (`runsc`) si Docker lo tiene registrado
y `runc` si no; `--runtime` lo fuerza. El contenedor va en una red interna de
Docker, sin salida a internet, con el sistema de archivos de solo lectura,
`--memory 1g --cpus 1 --pids-limit 256 --ipc none`, y sin más capacidades que
`SETUID`, `SETGID`, `KILL`, `CHOWN`, `FOWNER`, `DAC_OVERRIDE` y `SYS_PTRACE` (el
corredor la usa para leer la memoria de los procesos del alumno). Se alcanza por
su IP, lo que funciona en Linux.

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
las mismas rutas de entrada que el despliegue, con un contenedor falso que anota
cada llamada, una base D1 local y un proveedor OAuth falso. No necesitan Docker
ni cuenta. Cubren las rutas, cada límite de [protection.md](protection.md), los
endpoints de [accounts.md](accounts.md), lo que se guarda de cada ejecución y la
limpieza diaria. Dos pruebas llaman al `siteverify` real de Turnstile con las
claves de prueba y se saltan si no hay red.

`tests/account_ui_test.py` arranca `runner/worker/test/serve.ts`, que sirve ese
mismo Worker en local con el proveedor falso, y lo recorre con un navegador. Se
ejecuta dentro de `mise run test:ui`.
