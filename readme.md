# Duo

Duo is a set of courses where you learn by writing and running code. Lessons are
narrated and animated, with exercises you run on the page, and your progress is
kept per account.

There are two courses, both in Spanish: **Qiskit**, on quantum computing, with
practice notebooks and a project that grows part by part, and **Física
computacional**, on numerical methods, by simulating oscillators, pendulums and
planets.

## Install

You need [mise](https://mise.jdx.dev/). It installs the tool versions that
`mise.toml` pins.

```sh
mise run install
```

This installs the Python and JavaScript dependencies, the browser the tests
drive and the original Qiskit guides.

## Run

```sh
mise run serve
```

This serves the courses at <http://localhost:8810/> and grades your code
exercises on your machine, without accounts. It needs no internet.

A Qiskit mission opens its practice notebook with a command such as:

```sh
uv run marimo edit practica/p1-quickstart.py
```

## Check

```sh
mise run check
```

This runs the linters, the type checks, the tests and the build check. It
changes no tracked file. `mise run fix` applies the safe fixes and the format.

`mise run test:integration` also builds the runner image and needs Docker, so
`check` does not run it.

## Deploy

```sh
mise run deploy
```

This publishes your own copy on Cloudflare. [docs/deploy.md](docs/deploy.md)
lists the accounts and values it needs first.

## More

[docs/readme.md](docs/readme.md) indexes the manual. To add a course, see
[Add a course](docs/lessons.md#add-a-course).
