# Drills

A drill is a short question the learner answers with a tap, for the casual mode:
sessions of 10 to 15 items, no audio, no keyboard. The code in
[`drill/`](../drill) holds the items, grades them and chooses the next session.
Every function is pure, so the browser runs it with no server call. The screen
that plays a session is in [`app/src/session/`](../app/src/session).

Text the learner sees (prompts, options, feedback) is in Spanish, because the
courses are.

## Item kinds

Every item has an `id`, the `lesson` it belongs to, a `prompt` and a `kind`. It
may have a `hint`. The schema is in [`drill/item.ts`](../drill/item.ts).

| Kind      | The learner                                  | Answer                           |
| --------- | -------------------------------------------- | -------------------------------- |
| `choice`  | Taps one option.                             | Index of the option.             |
| `numeric` | Enters a number, within `tol` of `answer`.   | A number, or text such as `0,5`. |
| `predict` | Bets on an outcome. Any option counts.       | Index of the option.             |
| `parsons` | Puts shuffled code lines in order.           | The lines, in the order chosen.  |
| `fill`    | Picks the token missing from a line of code. | Index of the option.             |
| `bug`     | Taps the wrong line of a snippet.            | Index of the line.               |

`grade(item, answer)` in [`drill/grade.ts`](../drill/grade.ts) returns
`{correct, feedback}`. Each kind also has its own function, such as
`gradeParsons`. An answer of the wrong shape is incorrect, with feedback that
asks the learner to answer.

- A `parsons` answer must match the lines exactly, indentation included. Its
  feedback counts the lines already in place. `parsonsPool(item, seed)` in
  [`drill/present.ts`](../drill/present.ts) gives the shuffled lines and
  distractors to show. The same seed gives the same order, and the order is
  never the solution.
- A `fill` item has 3 or 4 options. Its `code` holds one `___` where the token
  goes.
- A `predict` item has no right answer, because the lesson asks do not carry
  one. It is graded correct for any option, and its feedback is the lesson's
  `after` text.

## Where items come from

`mise run generate:items` writes `site/<course>/items.json` for each course. The
file is generated and git ignores it. It holds, lesson by lesson in the order of
`course.json`, first the asks of the lesson and then the authored items.

- **Asks.** The `choice`, `numeric` and `predict` asks of each
  `site/<course>/lessons/<id>/lesson.json` become items. Other asks are skipped.
  The id is `<lesson>:<kind>-<hash>`, where the hash is taken from the prompt.
  Reordering the beats or editing the options keeps the id. Changing the prompt
  makes a new item.
- **Authored items.** `parsons`, `fill` and `bug` items are written by hand.

## Author an item

Write the items of a lesson in `drill/items/<course>/<lesson>.json`. The file
name is the lesson id and must be a lesson of the course. The file holds a list:

```json
{
  "items": [
    {
      "kind": "fill",
      "id": "distancia-sol",
      "prompt": "¿Qué función da la distancia r al Sol?",
      "code": "import math\n\nprint(round(math.___(3, 4), 1))",
      "options": ["hypot", "sqrt", "dist", "atan2"],
      "right": 0,
      "why": "`math.hypot(x, y)` calcula la raíz de x² + y²."
    }
  ]
}
```

- `id` is local to the lesson: lowercase letters, digits and dashes. The build
  makes it `<lesson>:<id>`. Keep it when you edit the item, because the
  learner's review log refers to it.
- Do not write `lesson`. The file name sets it.
- `lang` is `python` (the default) or `qasm`.
- `parsons` has `lines` in the right order, each with its indentation. Optional
  `before` is code that stays first, such as imports. Optional `distractors` are
  lines that belong nowhere.
- `fill` has `code`, `options` and `right`.
- `bug` has `lines`, the index `bug` of the wrong line, and `fix`, that line
  corrected. `why` is required.
- Print something deterministic. Seed a sampler, or round a float.

`bun drill/build.ts` stops at the first invalid file. It names the path of the
file and each bad field, one per line, such as
`p1-patrones.json: items[1].right: right must be the index of an option`. A
misspelt key is an error too.

### The code is run

`mise run build:drill` runs the code of every authored item with the Qiskit and
numpy of the project environment, and checks Qiskit is 2.6. It fails if:

- the correct code of a `parsons`, `fill` or `bug` item does not run;
- swapping two neighbouring lines of a `parsons` item still runs with the same
  output, so the order would not be unique;
- a distractor is valid at no position, or a wrong `fill` option runs with the
  same output as the right one;
- a `bug` snippet runs with the same output with the bug as with the fix.

A `bug` snippet with the bug may fail or print something else. Both prove the
line is wrong.

## How a session is chosen

`planSession` in [`drill/schedule.ts`](../drill/schedule.ts) takes the bank, the
review log, the finished lessons and the time:

```ts
const items = await planSession({ bank, log, done, now: Date.now() });
```

- `log` holds one entry per answer: `{item, at, correct}`, with `at` in Unix
  milliseconds, in any order.
- `done` is the list of finished lessons. An item of any other lesson is never
  chosen, whether new or due.
- `size` is optional and the session never has more than 15 items.

The session is a pure function of its inputs. It holds, in this order:

1. The items due for review, the longest overdue first.
2. New items, which have no entry in the log, taken from the finished lessons in
   turn so one lesson does not fill the session.

A right answer counts as FSRS `Good` and a wrong one as `Again`. The scheduler
is [ts-fsrs](https://github.com/open-spaced-repetition/ts-fsrs) with FSRS-6 and
no learning steps, so intervals are whole days: a missed item is due the next
day, an item answered right for the first time in three, and then the intervals
grow with each right answer. A miss shortens the interval again.

A `predict` item is asked once, as a new item, and is never reviewed.

## The session

`/<course>/repaso/` plays a session, one item per screen. The path page of a
course with a finished lesson links to it from its review card, and the streak
in the header links to the last course the learner worked on. The page loads
`site/<course>/items.json`, asks `planSession` for the items and grades each tap
with `grade`.

- Every kind is answered by tap. `numeric` has an on-screen keypad with digits
  and a comma, so no keyboard opens; the schema rejects a negative `answer`,
  because the keypad has no minus. `parsons` places a line by tap and reorders
  by tap or by dragging the grip of a placed line.
- After each answer the screen says right or wrong, shows the correct answer of
  a miss and one line of why. A `predict` item says the bet was noted.
- A missed item comes back once at the end. A second miss adds nothing.
- The end shows the XP earned, the streak and a button back to the path. A
  learner with no account also sees "Guarda tu racha", with the sign-in links.
  That is the only place the screen asks for an account.

XP: 2 for an item right the first time and 1 for a miss answered right at the
end. The XP goes to the streak record of the browser (`rising:xp`) and, for a
signed-in learner, to `POST /api/xp` ([accounts.md](accounts.md#xp)).

The first answer to each item goes to the review log, `<course>:repaso`, a list
of `{item, at, correct}` that the scheduler replays. `site/progress.ts` keeps
the 4 latest answers of an item and 800 in all. The log and the XP are written
when the session ends: leaving earlier saves nothing.

## Tests

`bunx vitest run drill app/src/session` runs the graders, the extraction, the
validation of authored items, the scheduler and the rules of a session.
`mise run test:tools` includes them. `bun tests/session_test.ts` plays a session
of every kind in a browser at 390 and 360 px wide.
