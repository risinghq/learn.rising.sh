# Diseño

El catálogo (`site/index.html`), la portada del curso de Qiskit
(`site/qiskit/index.html`), la página de privacidad y el reproductor
(`site/qiskit/lesson.html`) comparten un solo tema. La marca del catálogo es
«Duo» y la del curso, «Qubit a qubit». Este documento dice qué tokens existen,
cómo se usan y qué medidas fijan la lectura.

La dirección es la de un programa de estudios impreso: una columna de lectura,
un serif con matiz de libro, filetes finos en lugar de tarjetas y un solo acento
violeta. La tinta y la superficie salen del mismo matiz que el acento.

## Archivos

| Archivo                 | Contenido                                                     |
| ----------------------- | ------------------------------------------------------------- |
| `site/theme.css`        | Tokens, la barra superior, los botones y `<progress>`.        |
| `site/theme.js`         | Fija el modo antes de pintar y construye el botón de tema.    |
| `site/catalog.css`      | Estilos del catálogo.                                         |
| `site/qiskit/index.css` | Estilos de la portada del curso y de la página de privacidad. |
| `site/qiskit/app.css`   | Estilos del reproductor.                                      |
| `tests/theme_test.py`   | Prueba de navegador: contraste, páginas, modo guardado.       |

Cada página carga `theme.css` antes de su propia hoja y `theme.js` en `<head>`.
Las del curso los enlazan como `../theme.css` y `../theme.js`. Todas tienen un
enlace para saltar al contenido y un único `<main id="main">`.

## Modo

El lector elige claro u oscuro y la elección se guarda en `localStorage`:

| Clave          | Valores         | Sin guardar                 |
| -------------- | --------------- | --------------------------- |
| `qiskit:theme` | `light`, `dark` | La preferencia del sistema. |

Con un valor guardado, `theme.js` lo copia a `data-theme` de `<html>` antes de
que el navegador pinte. Sin él, `<html>` no lleva `data-theme` y
`color-scheme: light dark` hace que cada `light-dark()` siga al sistema. Todo
elemento `[data-theme-ctl]` recibe un botón que ofrece el otro modo. Su texto
sale del atributo `lang` de la página: inglés en el catálogo y español en el
curso. Al cambiar de modo, `theme.js` lanza el evento `themechange` en `window`;
`engine.js` lo usa para volver a dibujar los lienzos.

## Color

`theme.css` define el color en OKLCH con un solo matiz, `--hue` (290). Dos
escalas de doce pasos salen de él: los neutros `--n1` a `--n12` y el acento
`--a1` a `--a12`. `--k` ajusta la croma del acento a lo que cabe en sRGB para
ese matiz. Cada paso guarda su valor claro y su valor oscuro con `light-dark()`.
Cambiar `--hue` cambia el tema entero.

Las hojas de componentes leen los roles, no los pasos:

| Token                                     | Uso                                                                 |
| ----------------------------------------- | ------------------------------------------------------------------- |
| `--bg`                                    | Fondo de la página.                                                 |
| `--bg2`                                   | Código en línea, botones y casillas. `--code-bg` vale lo mismo.     |
| `--card`                                  | Paneles y tarjetas. `--fig-bg` y `--node` valen lo mismo.           |
| `--stage`                                 | Escenario del reproductor. Es también el texto sobre un color dado. |
| `--line`                                  | Filetes y separadores.                                              |
| `--edge`                                  | Borde de un control. Alcanza 3:1 sobre las superficies.             |
| `--ink`                                   | Texto principal. `--fg` vale lo mismo.                              |
| `--muted`                                 | Texto secundario.                                                   |
| `--acc`, `--acc-hover`, `--acc-ink`       | Relleno del botón principal, su estado al pasar y el texto encima.  |
| `--acc-text`                              | El acento cuando es texto: enlaces y estados.                       |
| `--bad`                                   | Error. `--red` vale lo mismo.                                       |
| `--focus`                                 | Anillo de foco.                                                     |
| `--blue`, `--teal`, `--violet`, `--green` | Colores con nombre del reproductor.                                 |
| `--gold`                                  | Énfasis y etiquetas de pregunta.                                    |
| `--font`, `--mono`                        | Newsreader para el texto y los títulos; JetBrains Mono para código. |

### Colores con nombre

El reproductor llama a los colores de las lecciones por su nombre: `fg`,
`muted`, `blue`, `gold`, `teal`, `red`, `violet`, `green`, `grid` y `axis`.
`engine.js` los convierte en `var(--nombre)` y en las macros de KaTeX `\fg{…}`,
`\blue{…}` y las demás, que aplican la clase `c-<nombre>` de `app.css`:

| Nombre                                    | Token de origen                   |
| ----------------------------------------- | --------------------------------- |
| `fg`                                      | `--ink`                           |
| `muted`                                   | `--muted`                         |
| `red`                                     | `--bad`                           |
| `gold`, `blue`, `teal`, `violet`, `green` | El token del mismo nombre.        |
| `grid`                                    | `--blue` mezclado con `--stage`.  |
| `axis`                                    | `--muted` mezclado con `--stage`. |

Otros tokens, como `--wire`, `--emph-bg`, `--cursor` y `--barrier`, se derivan
de los anteriores con `color-mix()` en `theme.css`. No tienen valor propio.

## Tipografía y espacio

- Una familia de texto, Newsreader, y una de código, JetBrains Mono. Las páginas
  las cargan de `site/vendor/fonts.css`, en variable y solo con los rangos
  `latin` y `latin-ext`. Las fórmulas usan las fuentes de KaTeX.
- Ocho tamaños, de `--t-xs` (12 px) a `--t-4xl` (48 px), en `rem`, para que el
  tamaño de texto del navegador siga valiendo. Dos pesos: 400 y 600.
- Nueve pasos de espacio, `--s1` (4 px) a `--s24` (96 px), y tres radios: `--r1`
  4 px, `--r2` 8 px y `--r3` 16 px.
- El escenario del reproductor mide 1280×720 y se escala por `transform`, así
  que sus tamaños son píxeles de diseño y no `rem`.

## Lectura

- La portada y la página de privacidad son una columna de `46rem`, con filetes
  entre secciones. No hay tarjetas ni insignias.
- La lección es el escenario, el subtítulo y los controles. El subtítulo mide
  `42rem` y cuatro líneas de alto fijo, para que el texto no mueva el escenario.
- Un ejercicio o una misión ocupa el escenario con desplazamiento vertical; el
  editor sigue a 16 px o más.
- El código en línea va a `0.875em` sobre `--bg2`; el bloque de código, sobre
  `--code-bg`.

## Progreso

- En la portada, cada parte tiene un `<progress>` con sus lecciones completadas
  y el curso tiene uno general. El estilo está en `theme.css`.
- En el reproductor, `#steps` es un `<input type="range">` con una etiqueta,
  «Paso N de M» y «, con pregunta» si el paso la tiene. Arrastrarlo salta a ese
  paso. Su relleno sigue a `--p`, que fija `engine.js`.

## Reglas de uso

- Un color de una hoja o de un script es un token: `var(--acc)`, nunca un valor
  hexadecimal. Un fondo translúcido se escribe con `color-mix()` sobre
  `transparent`.
- Un color nuevo se añade a `theme.css` con su valor claro y su valor oscuro y
  pasa `tests/theme_test.py` antes de usarse.
- En atributos SVG de presentación `var(--x)` no vale: `engine.js` lo pone como
  estilo. Un lienzo lee el color con `cssv('nombre')` cada vez que se dibuja.
- El texto va sobre `--bg`, `--bg2`, `--card` o `--stage` y alcanza 4,5:1 en las
  cuatro. Los colores de acento que se usan como texto también.
- Los ejes, los cables y el borde de un control llevan significado y alcanzan
  3:1 sobre las cuatro superficies. Las rejillas y los filetes son decoración y
  no se miden.
- Cada botón tiene un estado `:active`, y solo uno por pantalla va relleno con
  `--acc`.
- La marca es `<a class="brand">Qubit a qubit</a>` en el curso y
  `<a class="brand">Duo</a>` en el catálogo, con el estilo de `theme.css`.

## Contraste

Criterio: WCAG 2.x AA. El texto necesita 4,5:1; los ejes, los cables y el borde
de un control, 3:1. `tests/theme_test.py` lee cada token en el navegador, en los
dos modos, y falla si alguno queda por debajo. Cada celda es la peor razón entre
las cuatro superficies (`--bg`, `--bg2`, `--card`, `--stage`), y `acc-ink/acc`
es el texto del botón sobre su relleno.

| token         |  dark | light |
| ------------- | ----: | ----: |
| `ink`         | 14.00 | 15.22 |
| `muted`       |  7.73 |  6.52 |
| `acc-text`    |  9.32 |  7.24 |
| `gold`        | 10.17 |  4.90 |
| `red`         |  6.90 |  5.32 |
| `blue`        |  7.79 |  5.34 |
| `teal`        |  9.33 |  4.86 |
| `violet`      |  7.46 |  5.79 |
| `green`       |  9.43 |  4.92 |
| `acc-ink/acc` |  7.66 |  6.17 |
| `axis`        |  4.60 |  3.76 |
| `wire`        |  4.60 |  3.76 |
| `edge`        |  3.89 |  3.46 |

Para repetir la medición:

```sh
mise run install
uv run --group tools python tests/theme_test.py --table
```

La misma prueba carga el catálogo, la portada del curso y tres lecciones, cada
una en su primer y último paso, en los dos modos y a 1366x768 y 390x844. Exige
que la consola no registre errores y que ningún `#scene > .blk` quede fuera de
`#stage`. `--shots CARPETA` guarda una captura de cada carga.
