# Design

The catalog (`site/index.html`), the course home pages
(`site/<course>/index.html`), the privacy page and the player
(`site/<course>/lesson.html`) share one theme. The catalog brand is "Rising" and
each course has its own brand, which is the name in its pages. This document
lists the tokens, how they are used and the measures that fix legibility.

The direction is that of a printed syllabus: one reading column, a bookish
serif, thin rules instead of cards and a single violet accent. The ink and the
surface come from the same hue as the accent.

## Files

| File                    | Contents                                                |
| ----------------------- | ------------------------------------------------------- |
| `site/theme.css`        | Tokens, the top bar, the buttons and `<progress>`.      |
| `site/theme.ts`         | Sets the mode before paint and builds the theme button. |
| `site/catalog.css`      | Catalog styles.                                         |
| `site/course.css`       | Styles of the course home pages and the privacy page.   |
| `site/qiskit/index.css` | What only the Qiskit home page shows.                   |
| `site/player/app.css`   | Player styles.                                          |
| `tests/theme_test.ts`   | Browser test: contrast, pages, saved mode.              |

Each page loads `theme.css` before its own sheet and `theme.js` in `<head>`. The
course pages link them as `../theme.css` and `../theme.js`. `theme.js` is the
result of bundling `theme.ts` with `mise run generate:scripts`; Git does not
version it. Every page has a link to skip to the content and a single
`<main id="main">`.

## Mode

The reader picks light or dark and the choice is saved in `localStorage`:

| Key            | Values          | Not saved              |
| -------------- | --------------- | ---------------------- |
| `qiskit:theme` | `light`, `dark` | The system preference. |

With a saved value, `theme.ts` copies it to `data-theme` on `<html>` before the
browser paints. Without it, `<html>` has no `data-theme` and
`color-scheme: light dark` makes every `light-dark()` follow the system. Every
`[data-theme-ctl]` element gets a button that offers the other mode. Its text
comes from the page's `lang` attribute: English in the catalog and Spanish in
the course. When the mode changes, `theme.ts` fires the `themechange` event on
`window`; `engine.ts` uses it to redraw the canvases.

## Color

`theme.css` defines color in OKLCH with a single hue, `--hue` (290). Two
twelve-step scales come from it: the neutrals `--n1` to `--n12` and the accent
`--a1` to `--a12`. `--k` fits the accent chroma to what sRGB holds for that hue.
Each step stores its light value and its dark value with `light-dark()`.
Changing `--hue` changes the whole theme.

The component sheets read roles, not steps:

| Token                                                                   | Use                                                                                                                             |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `--bg`                                                                  | Page background.                                                                                                                |
| `--bg2`                                                                 | Inline code, buttons and boxes. `--code-bg` has the same value.                                                                 |
| `--bg3`                                                                 | A control while pressed, and the row under the pointer.                                                                         |
| `--card`                                                                | Panels and cards. `--fig-bg` and `--node` have the same value.                                                                  |
| `--stage`                                                               | Player stage. It is also the text on a given color.                                                                             |
| `--line`                                                                | Rules and separators.                                                                                                           |
| `--edge`                                                                | Border of a control. It reaches 3:1 on the surfaces.                                                                            |
| `--ink`                                                                 | Main text. `--fg` has the same value.                                                                                           |
| `--muted`                                                               | Secondary text.                                                                                                                 |
| `--acc`, `--acc-hover`, `--acc-active`                                  | Fill of the main button, at rest, under the pointer, pressed.                                                                   |
| `--acc-ink`                                                             | Text on those fills.                                                                                                            |
| `--acc-text`, `--acc-text-hover`                                        | The accent when it is text: links and states, and under the pointer.                                                            |
| `--shadow-ring`, `--shadow-raised`, `--shadow-overlay`, `--shadow-emph` | Depth in place of a border: a 1 px tinted ring, a raised surface, a menu or dialog, and the gold ring of an emphasised formula. |
| `--bad`                                                                 | Error. `--red` has the same value.                                                                                              |
| `--focus`                                                               | Focus ring.                                                                                                                     |
| `--blue`, `--teal`, `--violet`, `--green`                               | Named colors of the player.                                                                                                     |
| `--gold`                                                                | Emphasis and question labels.                                                                                                   |
| `--font`, `--mono`                                                      | Newsreader for text and titles; JetBrains Mono for code.                                                                        |

### Named colors

The player calls the lesson colors by name: `fg`, `muted`, `blue`, `gold`,
`teal`, `red`, `violet`, `green`, `grid` and `axis`. `engine.ts` turns them into
`var(--name)` and into the KaTeX macros `\fg{…}`, `\blue{…}` and the rest, which
apply the `c-<name>` class of `app.css`:

| Name                                      | Source token                    |
| ----------------------------------------- | ------------------------------- |
| `fg`                                      | `--ink`                         |
| `muted`                                   | `--muted`                       |
| `red`                                     | `--bad`                         |
| `gold`, `blue`, `teal`, `violet`, `green` | The token of the same name.     |
| `grid`                                    | `--blue` mixed with `--stage`.  |
| `axis`                                    | `--muted` mixed with `--stage`. |

Other tokens, such as `--wire`, `--emph-bg`, `--cursor` and `--barrier`, derive
from the ones above with `color-mix()` in `theme.css`. They have no value of
their own.

## Type and space

- One text family, Newsreader, and one code family, JetBrains Mono. The pages
  load them from `site/vendor/fonts.css`, as variable fonts with only the
  `latin` and `latin-ext` ranges. Formulas use the KaTeX fonts.
- Eight sizes, from `--t-xs` (12 px) to `--t-4xl` (48 px), in `rem`, so the
  browser's text size setting still applies. Two weights: 400 and 600.
- Nine steps of space, `--s1` (4 px) to `--s24` (96 px), and three radii: `--r1`
  4 px, `--r2` 8 px and `--r3` 16 px.
- The player stage is 1280×720 and scales by `transform`, so its sizes are
  design pixels and not `rem`.
- Counters (`.meta`, `.pr .n`, the lesson list, `.stepno`, `.score`) set
  `font-variant-numeric: tabular-nums`, so the digits do not shift as the value
  changes.

## Motion and states

Every duration and curve is a token in `theme.css`:

| Token                                               | Use                                                                            |
| --------------------------------------------------- | ------------------------------------------------------------------------------ |
| `--ease`                                            | Ease-out curve for entrances and movement.                                     |
| `--d-fast`, `--d-base`, `--d-slow`                  | 120, 180 and 280 ms: controls, menus and dialogs, panels.                      |
| `--d-reveal`                                        | 450 ms: a block that appears on the player stage.                              |
| `--tr-control`                                      | The transition of a control, with each property named.                         |
| `--press`, `--grab`, `--enter`, `--rise`, `--slide` | The transform of a press, a grabbed thumb, an entrance, a rise and a slide-in. |
| `--disabled`                                        | Opacity of a disabled control.                                                 |

- A transition lists the properties it changes. Nothing transitions `all`.
  Controls stay under 300 ms. Only `--d-reveal` is longer, and only on the
  stage, where the narration paces it.
- A press scales to 0.97. A menu or dialog enters from `scale(0.95)` with
  `@starting-style`, never from 0.
- A leaving block is faster than an entering one.
- With `prefers-reduced-motion: reduce`, the transform tokens become `none`.
  Colour and opacity changes stay, and the spinner slows down.
- Each button, link, course card and lesson row has a hover, a `:focus-visible`,
  an `:active` and, for a control, a disabled state. Hover applies only where
  the device has a pointer that hovers, so a touch never leaves a row
  highlighted. A disabled control, native or `aria-disabled`, drops to
  `--disabled` and shows `not-allowed`.
- The focus ring is `--focus`, 2 px, in both modes. It reaches 3:1 on every
  surface listed under Contrast.

## Reading

- The home page and the privacy page are one `46rem` column, with rules between
  sections. There are no cards or badges.
- The lesson is the stage, the subtitle and the controls. The subtitle is
  `42rem` wide and four lines of fixed height, so the text does not move the
  stage.
- An exercise or a mission fills the stage with vertical scrolling; the editor
  stays at 16 px or more.
- Inline code is `0.875em` on `--bg2`; the code block is on `--code-bg`.

## Progress

- On the home page, each part has a `<progress>` with its completed lessons and
  the course has an overall one. The style is in `theme.css`.
- In the player, `#steps` is an `<input type="range">` with a label, "Paso N de
  M" and ", con pregunta" if the step has a question. Dragging it jumps to that
  step. Its fill follows `--p`, which `engine.ts` sets.

## Rules of use

- A color in a sheet or a script is a token: `var(--acc)`, never a hexadecimal
  value. A translucent background is written with `color-mix()` over
  `transparent`.
- A new color is added to `theme.css` with its light value and its dark value
  and passes `tests/theme_test.ts` before it is used.
- In SVG presentation attributes `var(--x)` does not work: `engine.ts` sets it
  as a style. A canvas reads the color with `cssv('name')` each time it draws.
- Text sits on `--bg`, `--bg2`, `--bg3`, `--card` or `--stage` and reaches 4.5:1
  on all five. The accent colors used as text do too.
- Axes, wires and the border of a control carry meaning and reach 3:1 on the
  five surfaces. Grids and rules are decoration and are not measured.
- Every button has an `:active` state, and only one per screen is filled with
  `--acc`. The step that checks an exercise is that button; the one that moves
  on is not filled.
- The brand is `<a class="brand">Qubit a qubit</a>` in the course and
  `<a class="brand">Rising</a>` in the catalog, styled by `theme.css`.

## Contrast

Criterion: WCAG 2.x AA. Text needs 4.5:1; axes, wires and the border of a
control, 3:1. `tests/theme_test.ts` reads each token in the browser, in both
modes, and fails if any falls below. Each cell is the worst ratio among the five
surfaces (`--bg`, `--bg2`, `--bg3`, `--card`, `--stage`), and `acc-ink/acc` is
the button text on its fill.

| token            |  dark | light |
| ---------------- | ----: | ----: |
| `ink`            | 13.02 | 14.39 |
| `muted`          |  7.19 |  6.16 |
| `acc-text`       |  8.67 |  6.84 |
| `acc-text-hover` | 12.54 | 11.62 |
| `gold`           |  9.46 |  4.63 |
| `red`            |  6.42 |  5.03 |
| `blue`           |  7.25 |  5.04 |
| `teal`           |  8.68 |  4.60 |
| `violet`         |  6.94 |  5.48 |
| `green`          |  8.77 |  4.65 |
| `acc-ink/acc`    |  7.66 |  6.17 |
| `axis`           |  4.28 |  3.55 |
| `wire`           |  4.28 |  3.55 |
| `edge`           |  3.62 |  3.27 |

To repeat the measurement:

```sh
mise run install
bun tests/theme_test.ts --table
```

The same test loads the catalog, the course home page and three lessons, each at
its first and last step, in both modes and at 1366x768 and 390x844. It requires
that the console logs no errors and that no `#scene > .blk` falls outside
`#stage`. `--shots FOLDER` saves a screenshot of each load.
