"""Measure the cold and warm latency of POST /run with Docker.

    python runner/bench.py [--runs 50] [--runtime runc|runsc]

Cold: from `docker run` to the reply of the first check, in a new container.
Warm: the same request in a container that has already served one. Times are
client-side, in milliseconds. The image is already on disk, so a cold run does
not include pulling it.
"""

import argparse
import json
import statistics
import sys
import time
import urllib.request
from collections.abc import Iterable
from typing import Any

import local

EXERCISES = local.ROOT / "exercises"
WORKLOADS = {
    "run: print": {"code": "print('hola')"},
    "check: ghz (qiskit)": {
        "mode": "check",
        "exercise": "p1-quickstart/ghz",
        "code": (EXERCISES / "p1-quickstart/ghz/solution.py").read_text(),
    },
    "check: hasta-uno (aer)": {
        "mode": "check",
        "exercise": "p2-control-clasico/hasta-uno",
        "code": (EXERCISES / "p2-control-clasico/hasta-uno/solution.py").read_text(),
    },
}


def post(url: str, body: dict[str, str]) -> tuple[float, dict[str, Any]]:
    req = urllib.request.Request(
        f"{url}/run", json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    assert out["passed"], out
    return (time.monotonic() - start) * 1000, out


def summary(label: str, samples: Iterable[float]) -> str:
    values = sorted(samples)
    p95 = values[min(len(values) - 1, round(0.95 * len(values)) - 1)]
    return (
        f"| {label} | {len(values)} | {values[0]:.0f} | {statistics.median(values):.0f} "
        f"| {p95:.0f} | {values[-1]:.0f} |"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--runtime", choices=("runc", "runsc"))
    args = parser.parse_args()
    runtime = args.runtime or local.default_runtime()

    rows: list[str] = []
    for label, body in WORKLOADS.items():
        started: list[float] = []
        first: list[float] = []
        total: list[float] = []
        server: list[float] = []
        for _ in range(args.runs):
            t0 = time.monotonic()
            container = local.start(runtime=runtime)
            try:
                started.append((time.monotonic() - t0) * 1000)
                ms, out = post(container.url, body)
                first.append(ms)
                total.append((time.monotonic() - t0) * 1000)
            finally:
                container.stop()
        rows += [
            summary(f"cold, {label}, container start", started),
            summary(f"cold, {label}, first request", first),
            summary(f"cold, {label}, start + first request", total),
        ]

        container = local.start(runtime=runtime)
        try:
            post(container.url, body)
            warm = []
            for _ in range(args.runs):
                ms, out = post(container.url, body)
                warm.append(ms)
                server.append(out["ms"])
        finally:
            container.stop()
        rows += [summary(f"warm, {label}", warm), summary(f"warm, {label}, server-side ms", server)]
        print(f"done {label}", file=sys.stderr, flush=True)

    print(f"runtime: {runtime}, {args.runs} runs each\n")
    print("| case | n | min ms | median ms | p95 ms | max ms |")
    print("| --- | --- | --- | --- | --- | --- |")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
