# Protección del Worker

El Worker comprueba cada `POST /run` antes de arrancar el contenedor. Las
comprobaciones van en este orden, y la primera que falla responde sin que el
contenedor reciba nada:

1. El [límite por IP](#límite-por-ip).
2. El límite por usuario, si la petición trae una sesión de cuenta (`qg_auth`)
   que no es de un [mantenedor](#mantenedores).
3. El [tamaño](#tamaño-del-código) del cuerpo y del código.
4. El [presupuesto](#presupuesto) del mes y del día.
5. [Turnstile](#turnstile), si la petición no es de un mantenedor ni trae una
   sesión de Turnstile válida.

Una negativa lleva `{"error": "...", "reason": "..."}`. El editor muestra el
texto de `error` tal cual. Todos los valores salen de `env` en
[`cloudflare.config.ts`](../runner/worker/cloudflare.config.ts); cambiarlos es
editar ese archivo y desplegar. Un valor ausente o que no es un número positivo
hace que el Worker responda 500 `internal_error` y registre qué variable falló.

`GET /health` lo responde el Worker con 200 sin tocar un contenedor, para que
una petición sin límite no pueda mantener una instancia encendida.

## Límite por IP

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
uno anónimo. Las peticiones de `/auth` usan el límite por IP de
`AUTH_PER_MINUTE` ([accounts.md](accounts.md#endpoints)) y las de `/api` con
sesión, el límite por usuario.

Cada contador vive en un Durable Object `RateLimiter` que se nombra con un HMAC
de la etiqueta (`limiter` para una IP, `user`, `auth` o `api`), del día y de la
clave (la IP o el id del usuario). La clave del HMAC sale de `TURNSTILE_SECRET`,
así que el nombre no se puede volver a una IP ni a un usuario sin ese secreto.
El objeto guarda dos contadores, el del minuto y el del día, y borra su estado
cuando termina el día.

## Tamaño del código

| Variable         | Valor  | Significa                     |
| ---------------- | ------ | ----------------------------- |
| `MAX_CODE_BYTES` | 20 000 | Bytes UTF-8 del campo `code`. |

Un cuerpo mayor que seis veces el máximo más 1024 bytes responde 413 sin leerse
entero. Un cuerpo que no es JSON o no trae `code` como texto responde 400
`bad_request`. Un código mayor responde 413 `too_large` y el alumno ve «El
código ocupa 20001 bytes y el máximo son 20000.». El contenedor repite la
comprobación con `MAX_CODE` de `qgcheck/runner.py`; para cambiar el tope hay que
cambiar los dos.

## Presupuesto

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

`INSTANCE_TYPE` e `INSTANCES` se declaran una vez en `cloudflare.config.ts`, que
los usa para la instancia que despliega y para el Worker. No hay un precio que
editar: [`src/container.ts`](../runner/worker/src/container.ts) tiene la tarifa
de Cloudflare y las medidas de cada tipo.

### Qué cuesta una ejecución

Cloudflare factura la CPU solo mientras la instancia trabaja, y la memoria y el
disco durante todo el tiempo que está encendida, trabaje o no. La instancia se
apaga 60 s (`SLEEP_AFTER_SECONDS`) después de su última petición. Los segundos
se cobran en pasos de 10 ms. Con `standard-2` (1 vCPU, 6 GiB y 12 GB) un segundo
cuesta:

| Concepto             | Cuenta                          | USD por segundo |
| -------------------- | ------------------------------- | --------------- |
| CPU, solo trabajando | 1 × 0,00002                     | 0,00002         |
| Encendida, siempre   | 6 × 0,0000025 + 12 × 0,00000007 | 0,00001584      |

Una ejecución aislada de 2 s, sin otra en los 60 s anteriores, cuesta 2 ×
0,00002 de CPU más 62 s encendida × 0,00001584: 0,00102 USD. Casi todo es la
espera. Las ejecuciones que llegan con la instancia encendida solo alargan su
ventana.

El Worker aparta y cobra así, en el Durable Object `Budget`, que guarda el gasto
del mes y del día (este solo cuenta el público) y, por instancia, el instante en
que se espera que se apague (`awakeUntil`):

1. Antes de arrancar el contenedor aparta la ejecución más cara que cabe en
   `RESERVED_BUSY_SECONDS`: esos segundos de CPU y los segundos encendida desde
   `max(ahora, awakeUntil)` hasta `ahora + RESERVED_BUSY_SECONDS + 60 s`.
2. Si la reserva no cabe, no ejecuta ([Qué se rechaza](#qué-se-rechaza)).
   Comprobar y apartar es una sola operación del objeto, así que varias
   peticiones simultáneas no pueden apartar a la vez lo que solo cabe una vez.
3. Al terminar cambia la reserva por el coste medido: el tiempo que esperó al
   contenedor (el arranque incluido) a la tarifa de CPU y la ventana encendida
   hasta 60 s después de que respondió, y nunca más de lo apartado. Si otra
   ejecución alargó `awakeUntil` mientras tanto, esa parte sigue cobrada.
4. Una petición que se rechaza después de apartar (por Turnstile) devuelve la
   reserva entera.

`RESERVED_BUSY_SECONDS` es un tope y no una estimación. Cubre los 10 s de
trabajo de [runner.md](runner.md#límites), el arranque de una instancia y el
reintento tras un 503. Si la ejecución, con su reintento, llega a ese tiempo, el
Worker detiene la instancia que aún no había respondido, cobra lo apartado y
responde 504 `run_too_long`. El alumno ve «La ejecución tardó más de lo que el
corredor permite y se detuvo. Revisa si el código tiene un bucle sin fin.» Como
cada ejecución cuesta como mucho lo que apartó y solo se aparta si cabe, el
gasto estimado no pasa del presupuesto. Si el Worker se interrumpe entre apartar
y terminar, o falla el almacenamiento al terminar (se registra con
`where: "settle"` y la respuesta no cambia), la reserva se queda y el mes cuenta
de más, nunca de menos.

La suma de `cost_nano_usd` en el
[registro](#qué-recibe-el-contenedor-y-qué-se-registra) da el gasto estimado del
mes. La estimación ignora las cuotas mensuales incluidas en Workers Paid y cobra
la CPU de todo el tiempo que la petición esperó al contenedor. Una instancia que
el Worker no logra detener al llegar al tope (se registra con `where: "stop"`)
se factura hasta que se apague sola, y queda fuera de la cuenta.

### Qué se rechaza

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

Con el presupuesto de 2 USD, quien no mantiene el sitio dispone de 1,5 USD al
mes y de 0,10 USD (1,5 entre 15) al día.

### Mantenedores

`MAINTAINERS` es una lista de ids numéricos de GitHub separados por comas, sin
logins: un login se puede renombrar y otra persona puede quedárselo, y el id no
cambia. Con la lista vacía nadie es mantenedor. Quien entró con GitHub y tiene
su id en la lista es mantenedor. No pasa por Turnstile, no tiene el límite por
usuario y gasta del presupuesto entero. El límite por IP y el tamaño del código
siguen valiendo para él. Una cuenta de Google nunca es mantenedora, aunque su
identificador sea el mismo número. Un valor que no sea una lista de ids hace que
el Worker responda 500 y registre `MAINTAINERS`.
[deploy.md](deploy.md#9-elige-los-mantenedores) dice cómo ver el id de una
cuenta.

## Turnstile

Cloudflare Turnstile se verifica en la primera ejecución de cada sesión, con
cuenta o sin ella. Solo un mantenedor no pasa por Turnstile: la petición ni
llama a `siteverify` ni recibe `qg_session`. Una petición sin sesión de
Turnstile y sin token recibe 403 `turnstile_missing` con la clave del sitio en
el campo `sitekey`. Con ella, `site/qiskit/exercise.js` carga el widget y repite
la petición con el token en la cabecera `X-Turnstile-Token`. El Worker lo
comprueba con `siteverify`, al que envía solo el secreto y el token, y si vale
responde con la cookie `qg_session` además del resultado:

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

`TURNSTILE_SECRET` es un secreto del Worker. La clave del sitio no es secreta:
el Worker se la da a la página en la respuesta `turnstile_missing`. Con
`TURNSTILE_SITE_KEY` vacía, un `POST /run` anónimo responde 500 `internal_error`
y registra la variable que falta. Cloudflare documenta claves de prueba que no
necesitan cuenta, y las pruebas del Worker usan los tres secretos:

| Clave                                 | Tipo    | Comportamiento                                                |
| ------------------------------------- | ------- | ------------------------------------------------------------- |
| `1x00000000000000000000AA`            | sitio   | Siempre pasa. El token que genera es `XXXX.DUMMY.TOKEN.XXXX`. |
| `1x0000000000000000000000000000000AA` | secreto | Siempre pasa.                                                 |
| `2x0000000000000000000000000000000AA` | secreto | Siempre falla.                                                |
| `3x0000000000000000000000000000000AA` | secreto | Responde que el token ya se usó.                              |

## Qué recibe el contenedor y qué se registra

El contenedor recibe el cuerpo de la petición y `Content-Type`. No recibe la
cookie, el token ni la IP.

El Worker escribe estos registros y ningún otro. Todos tienen campos fijos, que
[`src/log.ts`](../runner/worker/src/log.ts) define.

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
   - `"attempt"`: falló anotar el intento en la base.

4. Una línea de error con `event` `auth`, `api` o `purge` cuando falla un
   endpoint de [accounts.md](accounts.md) o la limpieza diaria. Lleva `outcome`
   `internal_error`, `status` 500 y `error` con el nombre de la clase. Un
   endpoint responde 500 `internal_error`; la limpieza deja que falle el cron.

Ningún registro lleva el código, la IP, el token, la cookie ni el texto de un
error. `cloudflare.config.ts` activa Workers Logs con el registro de
invocaciones apagado, que es el que lleva la petición. Lo que Cloudflare guarda
de su red no depende del Worker.
