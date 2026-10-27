# Plan: from lessons to watch to lessons to do

Decided on 2026-10-07. Problem: the lessons are mostly for consuming (watch,
listen, answer one or two memory questions). Goal: each lesson leads the learner
to **act** and to **reflect**.

## 1. The new cycle of each lesson

| Moment      | What happens                                                                         | How it is implemented                                           |
| ----------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| **Predict** | Before seeing a result, you bet on an answer (counts, depth, expectation value).     | `ask` before the reveal, not after. At least one per lesson.    |
| **Watch**   | The current narrated animation, a little shorter.                                    | Same as today.                                                  |
| **Do**      | A mission in the lesson's marimo notebook.                                           | A "Your turn" step with the mission and the command to open it. |
| **Reflect** | One or two open questions: "explain it in your own words", "what would happen if…?". | A text box saved in the browser; it shows when you come back.   |
| **Recap**   | The current summary.                                                                 | Same as today.                                                  |

## 2. Practice notebooks with marimo

- One notebook per lesson: `practica/<id>.py`, opened with
  `uv run marimo edit practica/<id>.py`.
- **Why marimo and not Jupyter?** It is reactive: you change something and
  everything recomputes, so the checks show ✅ or ❌ at once. It has sliders,
  which suit exploring parameters. Its files are plain `.py`: light, easy to
  version and checkable with `tools/verify.py`.
- **The downside:** the IBM guides and the community use Jupyter. A mission in
  Part I teaches how to convert between the two formats (`marimo convert`) so
  you can use Jupyter too.
- Exercises come in three levels: 🟢 reproduce · 🟡 modify · 🔴 create. Each has
  its own check.
- Qiskit does not run in the browser, so the notebooks run on your machine, in
  the project's uv environment.

## 3. A project through the course: the spin chain (Ising)

One experiment that grows part by part (`practica/proyecto/`), with a clear
physical goal: see how the magnetization of a spin chain evolves after a sudden
change of the field.

| Part | Project milestone                                                            |
| ---- | ---------------------------------------------------------------------------- |
| I    | Create the IBM Quantum account (Open plan). One Trotter step with 2 spins.   |
| II   | Hamiltonian as a `SparsePauliOp`; N-step circuit; magnetization observables. |
| III  | Transpile for `FakeFez`; compare levels; depth against number of steps.      |
| IV   | Magnetization over time: exact against noisy simulation (Aer).               |
| V    | **First run on a real QPU** (budget ≤ 1 min).                                |
| VI   | Mitigate: no mitigation against TREX and ZNE; how close to the exact value?  |
| VII  | Fractional gates (RZZ) and batch mode; second real run.                      |
| VIII | Reduce the depth with an addon (OBP or AQC-Tensor).                          |
| IX   | Migrate the code to the client-side primitives and package it.               |
| X    | Final reproducible report: plots, citation of Qiskit and of the QPU.         |

The Open plan budget is 10 minutes every 28 days. Three real runs are planned,
about 1–2 minutes each. Before each one, the usage is estimated with the formula
from lesson 7.5.

## 4. Spaced review

The home page offers 3–4 questions a day from lessons already completed (the
existing `ask` questions), spaced in time: 1, 3, 7 and 21 days. The ones you
miss come back sooner.

## 5. New home page (a dashboard, not an index)

The structure of proposal C, but **with its own identity**: without IBM's blue
or typeface, and without the cream and serif style. Sections:

1. **Next action**: the pending lesson or the project mission.
2. **Ising project**: milestones with their state.
3. **Today's review**.
4. **Parts**: cards with a progress ring.

Pending: choose a name and palette from 2–3 variants.

## 6. Order of work

1. **Pilot**: apply the full cycle to 2 lessons (1.4 "Your first circuit" and
   2.1 "Building circuits"), with their 2 notebooks and milestone I of the
   project. You try them and give your opinion.
2. Adjust according to your opinion. Design the home page (identity variants).
3. Extend to all 63 lessons, part by part, checking notebooks and audio.
