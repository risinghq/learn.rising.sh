# Code exercises

An exercise is code that the learner writes and a grader checks. The grader,
`qgcheck`, runs on the machine and needs no network.

Text the learner sees (statements, hints, case names, failure messages and
button labels) is in Spanish, because the course is. The examples below keep it
that way.

## An exercise on disk

Each exercise is a folder `exercises/<lesson>/<exercise>/`. The name of the
lesson folder is the `id` of the lesson.

| File          | Contents                                             | Reaches `site/`                 |
| ------------- | ---------------------------------------------------- | ------------------------------- |
| `starter.py`  | The code the learner sees when opening the exercise. | Yes                             |
| `solution.py` | The reference. It must pass every case.              | No                              |
| `check.py`    | The cases. Each `test_*` function is a case.         | Only the names of visible cases |

## Declare it in the lesson

`Exercise()` from [`lib.py`](../lessons_src/lib.py) creates the block. It goes
in the scene of a step, next to the `Mission` card, and is revealed with a
`show` action like any hidden block:

```python
Exercise(
    "p1-quickstart/ghz",
    "Escribe `ghz(n)`: un circuito de `n` qubits, medido con `measure_all()`.",
    level=3,
    needs="qiskit",
    id="e3",
    hidden=True,
    hints=["Empieza con una Hadamard en el qubit 0."],
)
```

| Field   | Meaning                                                                               |
| ------- | ------------------------------------------------------------------------------------- |
| `level` | 1 reproduce, 2 modify, 3 create.                                                      |
| `needs` | `"qiskit"` if the code runs with Qiskit alone, `"aer"` if it also needs `qiskit-aer`. |
| `hints` | Hints in order, from the vaguest to the most concrete.                                |

[`build.py`](../lessons_src/build.py) completes the block with `starter` and
with `cases`, the list of names of the visible cases, and writes it to
`lesson.json`. It does not publish `solution.py` or the hidden cases. It fails
if the exercise is not in the folder of its lesson, if a file is missing, if no
case is visible, if two blocks use the same exercise or if a folder of
`exercises/` appears in no lesson.

## Write `check.py`

```python
from qgcheck import counts, learner, visible


@visible("n = 2, 3 y 4")
def test_small():
    for n in (2, 3, 4):
        got = sorted(counts(learner.ghz(n)))
        assert got == ["0" * n, "1" * n], f"Con n = {n} salen {got}."


def test_larger():  # no @visible: the case is hidden
    for n in (5, 7):
        got = sorted(counts(learner.ghz(n)))
        assert got == ["0" * n, "1" * n], f"Con n = {n} salen {got}."
```

- The `assert` message is the error text the learner sees. A hidden case shows
  as `caso oculto 1`, `caso oculto 2`… with its message. What it must say is set
  by the [content rules](#content-rules).
- `@hint(n)` links a case, visible or hidden, to hint `n` of `hints` (the first
  is 1). If the case fails, the learner sees that hint next to it.
  `tools/exercises.py` rejects an `n` greater than the number of hints of the
  exercise.
- `learner.<name>` returns what the learner's code defined. If it did not define
  it, the case fails with "Falta definir `<name>` en tu código.". It is read
  inside the case, not when importing `check.py`: `build.py` imports the file to
  read the cases and `learner` does not yet have any learner's code.
- The learner's code runs in another process and only data reaches the cases:
  numbers, strings, lists, tuples, dictionaries with string keys, `bytes`, NumPy
  arrays, `Statevector`, `Operator`, `SparsePauliOp` and `QuantumCircuit`. A
  value of another type fails with "`<name>` contiene un valor de tipo `<Type>`
  que no se puede comprobar.". A case that needs to pass a class, a
  `PassManager` or a `Target`, or to read some axes, does it in a function of
  `check.py` with `@inside`: it runs in the learner's process, reads `learner`
  from there and receives and returns data.

  ```python
  from qgcheck import inside, learner, visible


  @inside
  def swaps_left(circuit):
      return PassManager([learner.SwapACx()]).run(circuit).count_ops().get("swap", 0)


  @visible("ningún swap")
  def test_no_swap():
      assert swaps_left(circuit_with_swaps()) == 0, "Todavía quedan swaps."
  ```

  The learner can alter what runs in their process, so an `@inside` function
  only obtains data: the comparison with the expected value and the `assert` go
  outside it.

- Any exception other than `AssertionError` in a case fails with "Tu código
  lanzó `<Type>`: `<message>`". If the case had called a function of the
  learner, it adds "Pasó al usar `ghz(7)`." with that last call, so a hidden
  case says which input it failed with even if the `assert` was never reached.
  The `qgcheck` helpers fail the same way: `counts` with no measurements gives
  "El circuito no mide ningún qubit… Pasó al usar `ghz(7)`.".
- Compare states, not circuit text: `state(circuit).equiv(...)` removes the
  final measurements. For sampling, use a fixed seed and a tolerance of at least
  four standard deviations.
- A prediction exercise leaves `prediccion` with no value (`None` or `""`) in
  the starter code. The visible case compares the bet with what the learner's
  circuit computes, not with a constant, and a hidden case checks that the
  lesson's circuit is unchanged, so the learner cannot be right by changing the
  circuit.
- An exercise that draws returns the figure or the axes, and the case reads what
  is behind it (for example `axes.patches` and the axis labels), not pixels. The
  runner runs with `MPLBACKEND=Agg` and its image includes `matplotlib`.

The helpers in [`qgcheck/__init__.py`](../qgcheck/__init__.py) import Qiskit
only when called:

| Helper                         | Returns                                                                                               |
| ------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `counts(circuit)`              | Counts of the first classical register with `StatevectorSampler`.                                     |
| `aer_counts(circuit)`          | The same with Aer's `SamplerV2`, for circuits with control flow.                                      |
| `gates(circuit)`               | `Counter` of operation names, including those inside `if_test` and `while_loop`.                      |
| `state(circuit)`               | `Statevector` of the circuit without its final measurements.                                          |
| `unsupported(circuit, target)` | List of the instructions the `Target` does not allow where they are, such as `['cz en 0-2']`.         |
| `operator(circuit)`            | `Operator` over the virtual qubits: applies the layout of a transpiled circuit, even a 156-qubit one. |

## Content rules

These rules hold for each exercise and for the lesson step that contains it.

1. **A question does not give away the next step.** The text of a question
   (`choice`, `numeric`, `reveal`, `predict`), its `why` and its `after` do not
   say what the exercise that comes next does. If they do, the exercise is
   already solved when it opens.
2. **Hints go in this order: idea, place, shape.** First they say which idea to
   use, then in which part of the code it goes and last the shape of the line,
   with blanks. None contains the solved line: that is `solution.py`.
3. **A hidden case message names the input that failed and what the learner's
   code returned, and never the expected value.** For example,
   `Con n = 7 salen ['0000000', '0000011'].` The learner reproduces the failure
   with that input without reading the answer. A message that shows the expected
   value leaves the hidden case with no effect.
4. **A level 3 statement names each argument and the trap, or follows a solved
   case.** A learner who creates code cannot guess the order of the arguments or
   what the grader measures. The statement says what the function receives and
   returns, and warns of the error that the hidden case does detect, or includes
   a worked example with values.
5. **A step with `Exercise` does not mention a notebook or a "green mark".** The
   exercise is checked with the **Comprobar** button of the page itself. Those
   words belong to `Mission`, which points to a marimo notebook.
6. **A part with a project milestone in the browser ends in a `pN-cierre`
   lesson.** It has a short review, with `choice` and `numeric` questions from
   the lessons of the part, and a level 3 exercise taken from the milestone,
   with a `solution.py` with the same logic as the milestone solution. The parts
   whose milestone needs an account or a QPU have no closing lesson.

## Grade code

```python
from qgcheck import grade

grade("p1-quickstart/ghz", code, mode="check")
```

[`qgcheck/runner.py`](../qgcheck/runner.py) writes the code to a temporary
directory and runs it with [`qgcheck/job.py`](../qgcheck/job.py) in a separate
process, the same job the runner launches. `mode="run"` only runs the learner's
code; `mode="check"` also runs the cases. It returns:

```json
{
  "passed": false,
  "stdout": "listo\n",
  "error": null,
  "ms": 1180,
  "tests": [
    {
      "name": "n = 2, 3 y 4",
      "visible": true,
      "passed": false,
      "message": "Con n = 3 salen ['000', '011'], y deberían salir solo 000 y 111.",
      "hint": 1
    },
    {
      "name": "caso oculto 1",
      "visible": false,
      "passed": false,
      "message": "Con n = 5 salen ['00000', '00011'].",
      "hint": null
    }
  ]
}
```

`hint` is the number of the hint that the case names with `@hint`, or `null`.

- `error` carries the error of the learner's code, with its line when the error
  comes from a line, for example
  `NameError: name 'y' is not defined (línea 2: print(y))`. A timeout has no
  line. With an error, `tests` stays empty.
- The code may not weigh more than 20 000 bytes and stops at 10 s. Those 10 s
  count from when the process starts, with the libraries that the code and the
  cases import included. If it prints more than 64 KiB, it stops.
- The parameter `block=("qiskit_aer",)` makes those modules impossible to import
  in the learner's process.
- `grade` does not isolate the learner from the machine: it limits no memory,
  processes or network. The learner's code runs in a process distinct from the
  one that runs the cases, but with the same user. A service exposed to the
  internet must run it in a container with no network and with limits:
  [runner.md](runner.md) does this.

## Editor in the lesson

[`exercise.js`](../site/qiskit/exercise.js) draws each `Exercise` block: the
statement, an editor with `starter.py` and the buttons **Ejecutar** (only runs
the code), **Comprobar** (also runs the cases), **Pista** and **Empezar de
nuevo**. It shows the output, the error, with its line marked in the editor if
it has one, and a ✓ or ✗ per case; hidden cases appear as `caso oculto N`. While
waiting for the runner, the buttons are disabled; if it takes long, it says so,
and at 30 s it gives up. Each failure (timeout, runner full, no network, invalid
response) has its own message.

- After **Comprobar**, the status counts the visible and the hidden cases
  separately: `Pasan 2 de 2 visibles · 0 de 2 ocultos.` An exercise with no
  hidden cases counts only the visible ones.
- If the code has an error, `tests` comes back empty. The panel shows the error
  (with its line, if it has one) and "No se pudo probar tu código", and lists no
  case.
- A case that fails and names a hint with `@hint` shows that hint under its
  message. It does not count as a hint requested with the **Pista** button.
- The editor is CodeMirror 6 with Python highlighting, with the colors of the
  page theme ([design.md](design.md)). `exercise.js` loads it only in the
  lessons that have an exercise.
- **Pista** shows one hint of `hints` per press. There is no button to see the
  solution: `solution.py` never leaves `exercises/`.
- Ctrl+Enter (⌘+Enter) runs, Ctrl+Shift+Enter checks, Tab indents and Esc
  followed by Tab leaves the editor. The lesson keys (space, arrows, `c`) do not
  act while typing.
- A step with an exercise is not scaled like the rest of the stage: it fills the
  screen and scrolls, so the editor can be used on a phone. It does not move to
  the next step by itself when the narration ends; the **Continuar** button does
  it.
- The code, the number of hints and checks and whether it was solved are saved
  in `localStorage`, under `qiskit:exercise:<exercise>`.

### Where the code runs

The editor sends `POST /run` with `{"exercise", "code", "mode"}` and receives
the result of `grade()`. The route is always `/run`, on the same origin as the
page. The runner of [runner.md](runner.md) does not answer `OPTIONS` requests or
send CORS headers, and its session cookie is `SameSite=Strict`: the page and the
runner must have the same origin. In production a single Worker serves them; see
[runner.md](runner.md#cloudflare-containers).

If the runner answers 403 with `reason` `turnstile_missing`, the page loads the
Cloudflare Turnstile widget with the site key that response carries, and repeats
the request with the token in the `X-Turnstile-Token` header. The widget shows
only if Cloudflare needs the reader to do something. With the session open it is
not requested again. If the widget does not load, the panel says so and the
reader can retry.

On your machine, [`tools/serve.py`](../tools/serve.py) answers `POST /run`
without Turnstile:

```sh
uv run python tools/serve.py [port]
```

It serves `site/` on `127.0.0.1` (port 8810 by default) and rejects a `POST`
that is not `application/json` or whose `Host` is not `localhost` or
`127.0.0.1`, so another website open in your browser cannot run code on your
machine.

### Rebuild the editor

`site/qiskit/editor.js` is the result of bundling [`editor/`](../editor) with
esbuild; it is versioned because `site/` is static. After changing
`editor/src/`:

```sh
mise run generate:editor
```

`mise run build:editor` fails if `site/qiskit/editor.js` does not match the
bundle that `editor/src/` would produce.

### Update KaTeX and the fonts

`site/vendor/` holds KaTeX and the Newsreader and JetBrains Mono fonts, copied
from the npm packages `katex` and `@fontsource-variable/*` of
`editor/package.json`. Git ignores it: `mise run install` generates it with
`editor/vendor.js`. To change a version:

```sh
bun add --cwd editor --exact katex@<version>
mise run generate:vendor
```

## Check the exercises

```sh
uv run python lessons_src/build.py
uv run python tools/exercises.py [lesson/exercise ...]
uv run pytest tests/exercises_test.py
uv run --group tools python tests/exercise_ui_test.py
```

[`tools/exercises.py`](../tools/exercises.py) reads from
`site/qiskit/lessons/*/lesson.json` which exercises exist, their `needs` and
their `hints`, so it goes after `build.py`. For each exercise it checks that:

1. `solution.py` passes every case.
2. `starter.py` runs without error and fails some case.
3. `needs` is true: with `"qiskit"`, `solution.py` passes without `qiskit_aer`;
   with `"aer"`, it does not pass without it.
4. Each `@hint(n)` names a hint that the exercise has in `hints`.

[`tests/exercises_test.py`](../tests/exercises_test.py) runs each exercise with
its solution and with a wrong solution that must fail with a useful message, and
with the wrong programs of `tests/mutants/<exercise>/` (the ones that make each
hidden case fail; they are complete programs, independent of the text of
`solution.py`), and checks that every hidden case that fails with the starter
code or with a wrong solution names its input. It also tests the grader, what
`build.py` publishes, the checks and `serve.py`.
[`tests/exercise_ui_test.py`](../tests/exercise_ui_test.py) opens the lessons in
the browser against `serve.py`: it writes wrong code and sees a case fail,
corrects it and sees it pass, reloads and checks that the progress remains. It
also writes a syntax error and a `ghz` that fails only hidden cases, and checks
what the panel shows. It repeats this on a phone, and tests the keyboard, the
hints, the timeout, the errors and the Turnstile check, with a test widget.
`mise run test:ui` runs the browser tests. All of them use
[`tests/offline.py`](../tests/offline.py): the browser aborts any request that
does not go to `127.0.0.1` or `localhost` and the test ends with an error that
names the address.
