# Command line

`rising` lets a learner write an exercise in their own editor, grade it on their
own machine and earn XP on the same account the site uses. It is the Python
package in [`cli/`](../cli). It grades with [`qgcheck`](../qgcheck), the grader
the site uses, and talks to the Worker's [routes](accounts.md#command-line).

## Run it

It needs [uv](https://docs.astral.sh/uv/). `uv` fetches the Python the package
needs (3.15 or later) and the course libraries on the first run.

```sh
uvx --from ./cli rising --help
```

From a clone of the repository, `./cli` is the folder. Without a clone, point
`--from` at the repository and keep `#subdirectory=cli` at the end of its URL.
`uvx` caches the package: add `--refresh` to get the newest exercises.

Every command prints in Spanish. `rising login` uses `https://learn.rising.sh`
unless `--url` or the `RISING_URL` variable names another site. Only `https` is
accepted, except for `localhost`, `127.0.0.1` and `::1`.

## Commands

| Command                           | What it does                                                         |
| --------------------------------- | -------------------------------------------------------------------- |
| `rising login`                    | Prints a URL and a code, waits for the approval and saves the token. |
| `rising logout`                   | Revokes the token on the site and deletes the saved copy.            |
| `rising pull <lesson>/<exercise>` | Writes the exercise into the current folder.                         |
| `rising test`                     | Grades the exercise of the current folder and prints each check.     |
| `rising submit`                   | Grades, and when every check passes, records the XP.                 |
| `rising status`                   | Prints the streak, the XP of today and the weekly board of friends.  |

### login

`rising login` asks the site for a code, prints the page to open and the code it
should show, and polls every 5 seconds. The learner opens the page, signs in
with Google or GitHub if the browser has no session, and presses «Aprobar». The
code lives 10 minutes. A learner who presses «Rechazar» or lets it expire gets
an error and no token.

The token is saved in `credentials.json` in the user's configuration folder
(`~/.config/rising` on Linux, set by `XDG_CONFIG_HOME`), readable only by its
owner. It is good for 90 days ([protection.md](protection.md#cli-tokens)). When
the site rejects it, a command says to run `rising login` again.

### pull

`rising pull p1-quickstart/ghz` writes three files in the current folder:

- `ghz.py`, the starter to edit.
- `enunciado.md`, the statement and the names of the visible checks.
- `.rising.json`, which tells `test` and `submit` which exercise the folder
  holds.

It reads the lesson from the site's static files, so it works without signing
in. It refuses to replace existing files unless `--force` is given. The hints
are not pulled.

### test and submit

Both run the checks of the exercise on the learner's machine, through `qgcheck`,
in a separate process with a 30-second limit. They print each check with ✓ or ✗,
the message of a failed check, and whatever the code printed. `test` exits 0
when every check passes and 1 when not.

The checks ship inside the package, which the site never serves, so a `rising`
older than an exercise says it does not know it. Update `rising` to grade it.

`submit` stops when a check fails. When all pass it posts
[`POST /api/xp`](accounts.md#xp) with `source` `cli`, the `ref`
`lesson:exercise`, an `amount` of 10 and the machine's time zone. The result is
self-reported: the Worker's daily caps bound it and nothing verifies it. The
same exercise earns XP once per UTC day.

## Develop it

`mise run test:worker` runs the end-to-end test
[`cli.test.ts`](../runner/worker/test/cli.test.ts). It builds the package with
`uv`, starts the Worker in the test harness and drives every command against it.
The test skips itself when `uv` is missing.

The package builds with hatch. [`cli/hatch_build.py`](../cli/hatch_build.py)
copies every `exercises/*/*/check.py` into the wheel, so build it from a full
checkout of the repository.
