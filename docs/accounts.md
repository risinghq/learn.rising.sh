# Cuentas y progreso

Una cuenta es opcional. Sin ella todo funciona y el progreso se queda en el
navegador (`localStorage`). Con ella el progreso se guarda en una base D1 y se
comparte entre dispositivos. Se entra con Google o con GitHub, sin contraseña.

## Endpoints

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

Cada endpoint de `/auth` cuenta contra un límite por IP: `AUTH_PER_MINUTE` (10)
por minuto y `RATE_PER_DAY` por día. Al pasarse responde 429 `rate_auth`. Cada
petición de `/api` con sesión cuenta contra el límite por usuario de
[protection.md](protection.md#límite-por-ip).

## Entrar

El inicio de sesión es el flujo de código de autorización de OAuth 2.0 con
`state` y PKCE (S256), escrito sin biblioteca en
[`src/auth.ts`](../runner/worker/src/auth.ts).

1. `GET /auth/<proveedor>` guarda un `state` al azar, el verificador PKCE y el
   `return` en la cookie `qg_oauth`
   (`Path=/auth; HttpOnly; Secure; SameSite=Lax`, 10 minutos) y redirige al
   proveedor. Google recibe el permiso `openid`; GitHub, ninguno. `return` solo
   puede ser una ruta de este sitio (empieza por una `/` y no por `//` ni `/\`,
   sin caracteres de control, hasta 200 caracteres); otra cosa responde 400
   `bad_return`. Sin las credenciales del proveedor responde 503
   `provider_unavailable`.
2. La vuelta cambia el código por un token en el extremo del proveedor y lee de
   su extremo de datos solo el identificador: `sub` en Google, `id` en GitHub.
   Cada llamada al proveedor espera 5 s como mucho.
3. Si el identificador ya tiene usuario, entra en él; si no, se crea uno. Una
   sesión nueva sale en la cookie `qg_auth`
   (`Path=/; HttpOnly; Secure; SameSite=Lax`, `AUTH_SESSION_DAYS` días, 30) y la
   respuesta redirige a `return`. La cookie `qg_oauth` se gasta en toda vuelta.

La vuelta se rechaza con 400 si falta la cookie `qg_oauth` o es de otro
proveedor (`flow_missing`), si el `state` no es el guardado (`state_mismatch`),
si no trae `code` (`code_missing`) o si el proveedor no acepta el código
(`code_rejected`). Si el proveedor no responde, 502 `provider_failed`. Si el
alumno cancela en la pantalla del proveedor, la respuesta redirige a `return`
sin sesión.

Un proveedor y un identificador son una identidad. Ni dos proveedores ni dos
cuentas de un mismo proveedor se juntan: cada identidad nueva es un usuario
nuevo. El `redirect_uri` sale del origen de la petición; qué registrar en cada
proveedor lo dice [deploy.md](deploy.md#4-crea-el-cliente-de-google).

## El progreso

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

Una escritura no quita nada y ninguna regla depende del orden, así que dos
dispositivos que se sincronizan acaban en el mismo estado. `POST /api/merge`
responde `{"progress": {...}}` con el resultado; `PUT /api/progress`
responde 204.

| Límite                      | Valor                                      | Respuesta          |
| --------------------------- | ------------------------------------------ | ------------------ |
| Tipo del cuerpo             | `application/json`                         | 415 `content_type` |
| Tamaño del cuerpo           | 800 000 bytes                              | 413 `too_large`    |
| Lecciones en el cuerpo      | 500                                        | 400 `bad_request`  |
| Ejercicios en el cuerpo     | 100                                        | 400 `bad_request`  |
| Claves de `kv` en el cuerpo | 2000                                       | 400 `bad_request`  |
| Valor de una clave de `kv`  | 64 000 bytes                               | 400 `bad_request`  |
| Elementos de una lista      | 1000                                       | 400 `bad_request`  |
| Código de un ejercicio      | 20 000 bytes                               | 400 `bad_request`  |
| Clave o campo desconocido   |                                            | 400 `bad_request`  |
| La cuenta tras juntar       | 500 lecciones, 100 ejercicios, 2000 claves | 413 `too_much`     |

Un campo desconocido responde 400 para que un error de la página se vea.

Dos escrituras a la vez del mismo usuario no se pisan. `mergeProgress` lee el
progreso y `users.progress_version` en un lote, calcula el resultado y lo
escribe en otro lote cuyas sentencias solo actúan si `progress_version` sigue
siendo la leída. Si otra escritura se coló, vuelve a leer y a juntar. Tras 10
intentos responde 503 `busy` con `Retry-After`.

`DELETE /api/me` borra el usuario y, por las claves foráneas, sus identidades,
sesiones, progreso e intentos. Responde `{"deleted": true}` y borra la cookie.

## En el sitio

[`site/qiskit/account.js`](../site/qiskit/account.js) es el cliente. Pone el
menú _Entrar_ en la cabecera de la portada del curso, de las lecciones y de
[`privacidad.html`](../site/qiskit/privacidad.html), la página que dice qué se
guarda, cuánto tiempo y cómo borrarlo.

- Sin cuenta, la página no hace ninguna petición salvo `/run`. Lo que mira para
  saberlo es la marca `qiskit:cuenta` de `localStorage`.
- _Entrar con Google_ y _Entrar con GitHub_ van a `/auth/<proveedor>` con
  `return` igual a la página actual más `#cuenta`. Al volver, ese `#cuenta` hace
  que la página deje la marca y junte el progreso.
- Con la marca, cada carga manda todo el progreso del navegador a
  `POST /api/merge` y guarda la respuesta antes de que la página lo lea. Espera
  4 s como mucho; si el Worker no responde, la página sigue con lo local. La
  primera vez que entras, esa misma llamada junta lo que ya había en el
  navegador con lo de la cuenta.
- Cada cambio se manda después, en `PUT /api/progress`, 1,5 s después del último
  y siempre al cerrar o ocultar la página. Sin red, el cambio queda en
  `localStorage` y la siguiente carga lo junta.
- Cada `qiskit:exercise:<id>` lleva `at`, la hora de la última edición del
  código. Solo cambia al cambiar el código. Así gana la copia más reciente al
  juntar.
- Se sincronizan las lecciones hechas, el código, las pistas y las
  comprobaciones de cada ejercicio y las claves de `kv` de la tabla. El texto de
  las reflexiones (`qiskit:reflect`) no sale del navegador. Un valor que el
  Worker rechazaría (un código de más de 20 000 bytes, por ejemplo) se omite del
  cuerpo, porque rechazaría todo el cuerpo.
- _Cerrar sesión_ llama a `POST /auth/logout` y _Borrar mi cuenta_, tras una
  confirmación, a `DELETE /api/me`. Ninguna de las dos toca lo que hay en el
  navegador. Una respuesta 401 quita la marca.

El progreso local pasa a la cuenta con la que se entra, sea cual sea. En un
equipo compartido, quien entra después junta lo que dejó quien usó el navegador
antes.

## Datos que se guardan

El Worker no guarda correo, nombre, avatar ni contraseña: no los pide al
proveedor y descarta lo que este devuelve. El esquema es
[`src/schema.sql`](../runner/worker/src/schema.sql); no hay migraciones, así que
un cambio de esquema es borrar la base y crearla de nuevo
([deploy.md](deploy.md#2-crea-la-base-de-datos)). Todo cuelga de `users` con
`ON DELETE CASCADE`.

| Tabla            | Qué guarda                                                                           |
| ---------------- | ------------------------------------------------------------------------------------ |
| `users`          | Un id al azar, el día de alta, el día de la última visita y la versión del progreso. |
| `identities`     | Proveedor e identificador del proveedor de cada usuario.                             |
| `sessions`       | El hash SHA-256 del token de `qg_auth` y su caducidad. Nunca el token.               |
| `lesson_done`    | Las lecciones terminadas y cuándo.                                                   |
| `exercise_state` | El código, las pistas, las comprobaciones y si pasó, por ejercicio.                  |
| `kv`             | Las claves de `localStorage` de la tabla de arriba.                                  |
| `attempts`       | Una fila por ejecución, con o sin cuenta.                                            |

Una visita es una petición con sesión a `/run` o a `/api`, o la vuelta de OAuth.
Sube `seen_day` a lo sumo una vez al día.

Cada respuesta 200 de `/run` escribe una fila en `attempts`, a partir del JSON
que devolvió el contenedor, que es quien califica el código. La fila lleva el
momento, el `user_id` (`NULL` sin cuenta), el ejercicio, el modo, el resultado
(`pass`, `fail`, `error` o `timeout`), los nombres de los casos que fallaron, el
nombre de la excepción de Python (o `other`, o `killed_memory`, `killed_disk`,
`killed_output` o `killed_scan`), `ms` y el tamaño del código en bytes. No lleva
el código, `stdout`, el texto del error ni el `message` de un caso, que pueden
repetir lo que escribió el alumno. Solo se anota una ejecución con `mode` `run`
o `check` y un `exercise` con la forma de un id de ejercicio. Un fallo al
escribir la fila se registra y la respuesta no cambia. Una fila no se modifica
después de escribirse.

## Retención

| Variable                 | Valor | Qué se borra                                        |
| ------------------------ | ----- | --------------------------------------------------- |
| `ATTEMPT_RETENTION_DAYS` | 180   | Los intentos de más de esos días.                   |
| `ACCOUNT_RETENTION_DAYS` | 730   | Las cuentas sin una visita en esos días (24 meses). |

Un cron diario (`17 3 * * *`, UTC) llama al manejador `scheduled` del Worker,
que borra en un solo lote los intentos vencidos, las sesiones caducadas y las
cuentas inactivas, en ese orden. Borrar una cuenta arrastra todo lo suyo.

## Dónde se atascan los alumnos

`tools/dashboard.py` lee la base con `wrangler d1 execute` y no escribe nada.

```sh
uv run python tools/dashboard.py --database-id <uuid>
```

Lee la base remota, con la sesión de `bunx wrangler login` (en `runner/worker`)
o `CLOUDFLARE_API_TOKEN`. `--local` lee la copia local de `--persist-to`;
`--database` nombra la base (por defecto `qiskit-guides`) y `QG_D1_ID` puede dar
el uuid. Imprime, para el periodo de `--since` a `--until` (días UTC, por
defecto los últimos 30), los usuarios nuevos, los que intentaron algo y los
intentos con y sin cuenta; las lecciones terminadas por lección; los ejercicios
con más comprobaciones fallidas y los casos que más fallan; y los ejercicios
aprobados con más pistas abiertas. Una comprobación fallida es un intento
`check` que no acabó en `pass`, y cuenta también sin cuenta. Las lecciones
terminadas y las pistas salen de las tablas de una cuenta, así que no cuentan a
nadie anónimo. `--json` imprime lo mismo como JSON y `--limit` fija las filas de
cada ranking (10 por defecto).
