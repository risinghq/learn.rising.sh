# Design

Values live in `site/theme.css`. This document names which token plays which
role and the rules a check cannot measure. A rule is added here when the same
correction is made twice.

## Overview

The shell (the catalog, the path page of each course and the privacy page) is
the app a learner opens every day: a sans face, large touch targets, one filled
action per screen. The player (`site/<course>/lesson.html`) shares its tokens
and shows a lesson on a stage. Surfaces are flat, a hairline ring in place of a
border, one accent hue, and type kept small and tight. Depth comes from a
surface step or a ring, not from a drop shadow.

## Files

| File                     | Contents                                                        |
| ------------------------ | --------------------------------------------------------------- |
| `site/theme.css`         | Tokens, the Inter face, the top bar, the buttons, `<progress>`. |
| `site/fonts/`            | Inter, self-hosted: one variable file per Latin range.          |
| `site/theme.ts`          | Sets the mode before paint and builds the theme button.         |
| `app/src/styles/app.css` | The shell.                                                      |
| `site/player/app.css`    | The player.                                                     |
| `tests/theme_test.ts`    | Browser test: contrast, pages, saved mode.                      |

Each page loads `theme.css` before its own sheet and `theme.js` in `<head>`.
`theme.js` is the result of bundling `theme.ts` with
`mise run generate:scripts`; Git does not version it. The shell sheets are
bundled into `site/assets/` by `mise run generate:app`. Every page has a link to
skip to the content and a single `<main id="main">`.

## Mode

The reader picks light or dark and the choice is saved in `localStorage`:

| Key            | Values          | Not saved              |
| -------------- | --------------- | ---------------------- |
| `rising:theme` | `light`, `dark` | The system preference. |

With a saved value, `theme.ts` copies it to `data-theme` on `<html>` before the
browser paints. Without it, `<html>` has no `data-theme` and
`color-scheme: light dark` makes every `light-dark()` follow the system. The
shell draws its own theme button in the header, and the player gets one from
every `[data-theme-ctl]` element. Its text comes from the page's `lang`
attribute, Spanish in every page. When the mode changes, `theme.ts` fires the
`themechange` event on `window`; `engine.ts` uses it to redraw the canvases.

## Colors

`theme.css` defines color in OKLCH with a single hue, `--hue`. Two twelve-step
scales come from it: the neutrals `--n1` to `--n12` and the accent `--a1` to
`--a12`. `--k` fits the accent chroma to what sRGB holds for that hue. Each step
stores its light value and its dark value with `light-dark()`. Changing `--hue`
changes the whole theme.

The component sheets read roles, not steps:

| Role                         | Token                                               |
| ---------------------------- | --------------------------------------------------- |
| Page                         | `--bg`                                              |
| Inline code, boxes           | `--bg2` (`--code-bg` is the same)                   |
| Control pressed, row hovered | `--bg3`                                             |
| Panels, cards                | `--card` (`--fig-bg` and `--node` are the same)     |
| Player stage                 | `--stage`                                           |
| Rules, separators            | `--line`                                            |
| Border of a control          | `--edge`                                            |
| Body text                    | `--ink` (`--fg` is the same)                        |
| Secondary text               | `--muted`                                           |
| Fill of the filled action    | `--acc`, `--acc-hover`, `--acc-active`              |
| Text on that fill            | `--acc-ink`                                         |
| Accent as text               | `--acc-text`, `--acc-text-hover`                    |
| Depth in place of a border   | `--shadow-ring`                                     |
| Raised surface               | `--shadow-raised`                                   |
| Menu or dialog               | `--shadow-overlay`                                  |
| Emphasised formula           | `--shadow-emph`                                     |
| Error                        | `--bad` (`--red` is the same)                       |
| Focus ring                   | `--focus`                                           |
| Lesson colors                | `--blue`, `--teal`, `--violet`, `--green`, `--gold` |
| Faces                        | `--font` for text and titles, `--mono` for code     |

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

## Typography

One face serves the shell and the player. `--font` is Inter with the system sans
as fallback, `--mono` is the system monospace. A page does not set its own
`--font`; `tests/theme_test.ts` fails if two pages render different faces.
Formulas use the KaTeX fonts.

| Role                         | Size token                              | Weight token  |
| ---------------------------- | --------------------------------------- | ------------- |
| Detail, meta, counter label  | `--text-sm`                             | `--w-regular` |
| Body                         | `--text-md`                             | `--w-regular` |
| Title of a unit or a card    | `--text-lg`                             | `--w-strong`  |
| Page title                   | `--text-2xl`                            | `--w-strong`  |
| Player stage and large marks | `--text-xl`, `--text-3xl`, `--text-4xl` | `--w-strong`  |

- Sizes are in `rem`, so the browser's text size setting applies. The player
  stage has a fixed design size and scales by `transform`; its sizes are design
  pixels.
- Counters (the streak and the XP of the header, `.num`, `.stepno`, `.score`)
  set `font-variant-numeric: tabular-nums`, so the digits do not shift as the
  value changes.

## Layout

- Space comes from `--space-1` to `--space-16`. Related items sit at `--space-2`
  or `--space-3`; groups at `--space-4` to `--space-8`; a page section at
  `--space-12`.
- `--control` is the height of a button, a header link and a menu item. `--tap`
  is the floor for every touch target in the shell, the skip link and the icon
  buttons included. `--marker` (in `app/src/styles/app.css`) is the width of the
  number or state mark at the start of a unit and a lesson.
- The shell is one column under a sticky header. The header holds the way back
  (a back arrow on a course, the brand elsewhere), the streak and the XP of
  today, the account button and the theme button.
- The player is the stage, the subtitle and the controls. The subtitle has a
  fixed number of lines, so the text does not move the stage. An exercise fills
  the stage and scrolls vertically.
- In the player, the top bar holds the brand, the account button and the theme
  button in one row at every width. Under the narrow breakpoint the speed,
  subtitle and effects controls move into a popover opened by "Ajustes" next to
  the step counter; over it they sit in the top bar.

## Elevation and Depth

- Cards and the unit list take `--shadow-ring` and no border. A divider between
  rows is a border in `--line`.
- A menu or a dialog takes `--shadow-overlay`. A raised surface takes
  `--shadow-raised`. Everything else is flat.
- The gold ring of an emphasised formula is `--shadow-emph`.

## Shapes

| Element                              | Token  |
| ------------------------------------ | ------ |
| Inline code, small marks             | `--r1` |
| Buttons, fields, rows                | `--r2` |
| Cards, the unit list, menus, dialogs | `--r3` |

## Motion

Every duration and curve is a token in `theme.css`:

| Token                                               | Use                                                                            |
| --------------------------------------------------- | ------------------------------------------------------------------------------ |
| `--ease`                                            | Curve for entrances and movement.                                              |
| `--d-fast`, `--d-base`, `--d-slow`                  | Controls; menus and dialogs; panels.                                           |
| `--d-reveal`                                        | A block that appears on the player stage, paced by the narration.              |
| `--tr-control`                                      | The transition of a control, with each property named.                         |
| `--press`, `--grab`, `--enter`, `--rise`, `--slide` | The transform of a press, a grabbed thumb, an entrance, a rise and a slide-in. |
| `--disabled`                                        | Opacity of a disabled control.                                                 |

- A transition lists the properties it changes. Nothing transitions `all`.
- A menu or dialog enters from `--enter` with `@starting-style`, never from
  nothing. A leaving block is faster than an entering one.
- With `prefers-reduced-motion: reduce`, the transform tokens become `none`.
  Colour and opacity changes stay, and the spinner slows down.
- Hover applies only where the device has a pointer that hovers, so a touch
  never leaves a row highlighted. A disabled control, native or `aria-disabled`,
  drops to `--disabled` and shows `not-allowed`.
- The focus ring is `--focus` in both modes.

## Components

Start a new screen from the one closest to it:

| Screen kind             | Start from                            |
| ----------------------- | ------------------------------------- |
| List of courses         | `app/src/components/Catalog.tsx`      |
| Path of one course      | `app/src/components/CoursePath.tsx`   |
| Project block on a path | `app/src/components/ProjectTrack.tsx` |
| Lesson player           | `site/qiskit/lesson.html`             |

| Need                        | Use                                           | Instead of                 |
| --------------------------- | --------------------------------------------- | -------------------------- |
| The one action of a screen  | `.btn.primary`                                | A second filled button     |
| A secondary action          | `.btn`                                        | A link styled as a button  |
| A low-weight action         | `.btn.quiet`                                  | A text link                |
| State of a lesson or a unit | `.badge`, `.dot`, `.hito`                     | A color alone              |
| A course or a unit progress | `<progress>` with the text "N de M lecciones" | A bar without a label      |
| An icon                     | Lucide, `aria-hidden`, beside a text          | An icon alone in a control |

Progress: on the path page and the catalog a course shows a `<progress>` with
its completed path lessons. Each unit shows its count and a bar. Guides do not
enter either total. In the player, `#steps` is an `<input type="range">` with a
label, "Paso N de M" and ", con pregunta" if the step has a question; its fill
follows `--p`, which `engine.ts` sets.

## Do's and Don'ts

- Do keep every color a token. A translucent background is `color-mix()` over
  `transparent`. A new color enters `theme.css` with its light value and its
  dark value and passes `tests/theme_test.ts` before it is used.
- Do read a color in a canvas with `cssv('name')` each time it draws. In SVG
  presentation attributes `var(--x)` does not work; `engine.ts` sets it as a
  style.
- Do give every button a `:active` state, and write hover and active selectors
  without a comma inside `:not()`: the gate splits a selector on commas.
- Do keep one filled action per screen.
  - Catalog: no card is filled until a course is started. Courses are equal
    until the learner has a reason to favour one. Then the course in progress,
    last used first, carries the filled button.
  - Path page: the Start, Continue or Review button under the title is the only
    filled control. The current lesson, the current milestone and the project
    buttons are outlined, not filled.
  - Player: the step that checks an exercise; the one that moves on is not
    filled.
- Do put the outcome of a course under its title and the Start button after it.
  A page that shows the outcome below the parts hides the reason to start.
- Do show the parts of a course as one list with hairline dividers, not as one
  card per part.
- Do label a form control in the DOM before the script runs. A label filled by
  script leaves an unnamed control until it does.
- Do not mark a state by color alone: a check, a lock or an outline goes with
  it.
- Do not use a second face, a hexadecimal value, or a size that is not a token.
- The brand is `<a class="brand">` in both the shell and the player, styled by
  `theme.css`.

## Contrast

Criterion: WCAG 2.x AA. Text meets the text level on `--bg`, `--bg2`, `--bg3`,
`--card` and `--stage`. Axes, wires and the border of a control meet the
non-text level on the same five. Grids and rules are decoration and are not
measured. `tests/theme_test.ts` reads each token in the browser, in both modes,
and fails if any falls below. The worst ratio among the five surfaces is the
number that counts, and `acc-ink/acc` is the button text on its fill.

To repeat the measurement and print the table:

```sh
mise run install
bun tests/theme_test.ts --table
```

The same test loads the shell pages (the catalog, the privacy page and the path
page of each course) and three lessons, each lesson at its first and last step,
in both modes and at a desktop and a phone size. It requires that the console
logs no errors, that no `#scene > .blk` falls outside `#stage`, that Inter loads
in the shell and that no control in the shell is under `--tap`. `--shots FOLDER`
saves a screenshot of each load.
