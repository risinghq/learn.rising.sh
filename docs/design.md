# Diseño

El catálogo (`site/index.html`), la portada del curso de Qiskit
(`site/qiskit/index.html`) y el reproductor (`site/qiskit/lesson.html`)
comparten un solo tema: tres fuentes y tres paletas, cada una en modo claro y
oscuro. La marca del catálogo es «Duo» y la del curso, «Qubit a qubit». Este
documento dice qué tokens existen y cómo se usan.

## Archivos

| Archivo                 | Contenido                                                          |
| ----------------------- | ------------------------------------------------------------------ |
| `site/theme.css`        | Los tokens de color y de fuente, la marca y el control de tema.    |
| `site/theme.js`         | Fija paleta y modo antes de pintar y construye el control de tema. |
| `site/catalog.css`      | Estilos del catálogo.                                              |
| `site/qiskit/index.css` | Estilos de la portada del curso.                                   |
| `site/qiskit/app.css`   | Estilos del reproductor.                                           |
| `tests/theme_test.py`   | Prueba de navegador: contraste, páginas, paleta guardada.          |

Cada página carga `theme.css` antes de su propia hoja y `theme.js` en `<head>`.
Las del curso los enlazan como `../theme.css` y `../theme.js`.

## Paleta y modo

El lector elige dos cosas y las dos se guardan una vez en `localStorage`:

| Clave           | Valores                          | Sin guardar                 |
| --------------- | -------------------------------- | --------------------------- |
| `qiskit:paleta` | `fosforo`, `cobre`, `medianoche` | `fosforo`                   |
| `qiskit:theme`  | `light`, `dark`                  | La preferencia del sistema. |

`theme.js` copia los valores a `data-paleta` y `data-theme` de `<html>` antes de
que el navegador pinte. `theme.css` define los tokens en seis bloques,
`[data-paleta="…"][data-theme="…"]`. Un valor guardado que no existe se ignora.

Todo elemento `[data-theme-ctl]` recibe un selector de paleta y el botón de
modo, uno junto al otro. Las tres páginas lo tienen en su barra superior. En
pantallas de 600 px o menos el selector muestra solo el color de acento de la
paleta. Las etiquetas del control salen en el idioma del atributo `lang` de la
página: inglés en el catálogo y español en el curso. Al cambiar paleta o modo,
`theme.js` lanza el evento `themechange` en `window`; `engine.js` lo usa para
volver a dibujar los lienzos.

Cada paleta cambia el fondo, la tinta y los acentos:

| Paleta       | Acento `acc` | Segundo acento `acc2` |
| ------------ | ------------ | --------------------- |
| `fosforo`    | verde lima   | turquesa              |
| `cobre`      | naranja      | violeta               |
| `medianoche` | turquesa     | rosa                  |

## Tokens

Los valores de cada paleta están en `site/theme.css`. Los tokens son los mismos
en las seis combinaciones.

| Token                                     | Uso                                                                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `--bg`                                    | Fondo de la página.                                                                                              |
| `--bg2`                                   | Fondo de código en línea, botones y casillas.                                                                    |
| `--card`                                  | Tarjetas y paneles. Los alias `--panel`, `--fig-bg`, `--code-bg` y `--node` valen lo mismo.                      |
| `--stage`                                 | Escenario del reproductor. También es el color del texto sobre un color con nombre, como la letra de una puerta. |
| `--line`                                  | Bordes y separadores.                                                                                            |
| `--ink`                                   | Texto principal. `--fg` vale lo mismo.                                                                           |
| `--muted`                                 | Texto secundario.                                                                                                |
| `--acc`, `--acc-ink`                      | Acento de la paleta y el texto que se pone encima.                                                               |
| `--acc2`, `--acc3`                        | Segundo y tercer acento. `--acc3` es el dorado.                                                                  |
| `--bad`                                   | Error. `--red` vale lo mismo.                                                                                    |
| `--blue`, `--teal`, `--violet`, `--green` | Colores con nombre del reproductor.                                                                              |
| `--glow`                                  | Resplandor de la tarjeta destacada.                                                                              |
| `--display`, `--sans`, `--mono`           | Fuentes de títulos, de texto y de código.                                                                        |

### Colores con nombre

El reproductor llama a los colores de las lecciones por su nombre: `fg`,
`muted`, `blue`, `gold`, `teal`, `red`, `violet`, `green`, `grid` y `axis`.
`engine.js` los convierte en `var(--nombre)` y en las macros de KaTeX `\fg{…}`,
`\blue{…}` y las demás, que aplican la clase `c-<nombre>` de `app.css`. Cada
nombre es un token y sale de la paleta activa:

| Nombre                            | Token de origen                   |
| --------------------------------- | --------------------------------- |
| `fg`                              | `--ink`                           |
| `muted`                           | `--muted`                         |
| `gold`                            | `--acc3`                          |
| `red`                             | `--bad`                           |
| `blue`, `teal`, `violet`, `green` | Valor propio de cada paleta.      |
| `grid`                            | `--blue` mezclado con `--stage`.  |
| `axis`                            | `--muted` mezclado con `--stage`. |

Otros tokens, como `--fg-soft`, `--line-strong`, `--wire`, `--emph-bg`,
`--box-bg` y `--seg`, se derivan de los anteriores con `color-mix()` en
`theme.css`. No tienen valor propio.

## Reglas de uso

- Un color de una hoja o de un script es un token: `var(--acc)`, nunca un valor
  hexadecimal. Un fondo translúcido se escribe con `color-mix()` sobre
  `transparent`.
- Un color nuevo se añade a `theme.css` en las seis combinaciones y pasa
  `tests/theme_test.py` antes de usarse.
- En atributos SVG de presentación `var(--x)` no vale: `engine.js` lo pone como
  estilo. Un lienzo lee el color con `cssv('nombre')` cada vez que se dibuja.
- El texto va sobre `--bg`, `--bg2`, `--card` o `--stage` y alcanza 4,5:1 en las
  cuatro. Los colores de acento que se usan como texto también.
- Las líneas de ejes y de cables llevan significado y alcanzan 3:1 sobre
  `--stage` y `--card`. Las rejillas y los bordes son decoración y no se miden.
- La marca es `<a class="brand"><span class="dot"></span>Qubit a qubit</a>` en
  el curso y `<a class="brand"><span class="dot"></span>Duo</a>` en el catálogo,
  con el estilo de `theme.css`. En el reproductor, en pantallas de 600 px o
  menos, el punto se oculta para dejar sitio al título.
- Los títulos usan `--display` (Bricolage Grotesque), el texto `--sans` (Inter)
  y el código `--mono` (JetBrains Mono). Las tres páginas las cargan de
  `site/vendor/fonts.css`, en variable y solo con los rangos `latin` y
  `latin-ext`. Las fórmulas usan las fuentes de KaTeX.

## Contraste

Criterio: WCAG 2.x AA. El texto necesita 4,5:1; los ejes y los cables, 3:1.
`tests/theme_test.py` lee cada token en el navegador, en las seis combinaciones,
y falla si alguno queda por debajo. Cada celda es la peor razón entre las cuatro
superficies (`--bg`, `--bg2`, `--card`, `--stage`); `axis` y `wire` se miden
sobre `--stage` y `--card`, y `acc-ink/acc` es el texto del botón sobre su
fondo.

| token         | fosforo dark | fosforo light | cobre dark | cobre light | medianoche dark | medianoche light |
| ------------- | -----------: | ------------: | ---------: | ----------: | --------------: | ---------------: |
| `ink`         |        15.08 |         14.33 |      14.69 |       14.63 |           14.56 |            14.88 |
| `fg-soft`     |        11.69 |         10.12 |      11.44 |       10.34 |           11.31 |            10.60 |
| `card-text`   |         9.73 |          7.75 |       9.54 |        7.88 |            9.43 |             8.08 |
| `muted`       |         5.94 |          4.80 |       5.93 |        5.03 |            5.77 |             4.87 |
| `acc`         |        13.27 |          4.63 |       7.35 |        4.62 |           11.55 |             4.61 |
| `acc2`        |         9.55 |          4.63 |       7.51 |        5.21 |            6.45 |             5.19 |
| `gold`        |        10.40 |          4.67 |      12.05 |        4.66 |           10.24 |             4.69 |
| `red`         |         6.96 |          4.63 |       7.00 |        5.36 |            6.35 |             5.40 |
| `blue`        |         7.99 |          4.92 |       7.85 |        4.90 |            7.82 |             4.93 |
| `teal`        |         9.55 |          4.63 |       9.20 |        4.68 |           11.55 |             4.61 |
| `violet`      |         7.64 |          5.23 |       7.51 |        5.21 |            7.48 |             5.25 |
| `green`       |        10.03 |          4.69 |       9.86 |        4.67 |            9.82 |             4.70 |
| `acc-ink/acc` |        12.89 |          5.41 |       7.57 |        5.41 |           11.34 |             5.36 |
| `axis`        |         3.86 |          3.24 |       3.86 |        3.34 |            3.76 |             3.28 |
| `wire`        |         3.86 |          3.24 |       3.86 |        3.34 |            3.76 |             3.28 |

Para repetir la medición:

```sh
mise run install
uv run python tests/theme_test.py --table
```

La misma prueba carga el catálogo, la portada del curso y tres lecciones, cada
una en su primer y último paso, en las seis combinaciones y a 1366x768 y
390x844. Exige que la consola no registre errores y que ningún `#scene > .blk`
quede fuera de `#stage`. `--shots CARPETA` guarda una captura de cada carga.
