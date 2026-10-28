"""Measure what the solutions of the exercises ask of a runner instance.

    python runner/sizing.py [--types basic standard-1 standard-2] [--warm 3]
                            [--exercises p3-niveles/fidelidad ...] [--out FILE]

Each exercise on each type runs in a new container limited to the CPU and memory of that
Cloudflare instance type (`--cpus`, `--memory`). The container serves the solution once cold
and then `--warm` more times. Without `--exercises` it measures every solution.

The output is JSON: one record per request with the client latency, the runner's own `ms`
and `peak_mb`, the CPU the container used (cgroup `cpu.stat`), and per container the start
time and the memory peaks. `memory_peak_mb` is the cgroup's `memory.peak`, which counts the
page cache. `memory_anon_mb` is the largest sample of the memory without cache.
"""

import argparse
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import local

# The vCPU and GiB of `INSTANCE_TYPES` in runner/worker/src/container.ts.
TYPES = {
    "lite": ("0.0625", "256m"),
    "basic": ("0.25", "1g"),
    "standard-1": ("0.5", "4g"),
    "standard-2": ("1", "6g"),
}
MIB = 1024 * 1024


def solutions() -> list[str]:
    return sorted(
        str(p.parent.relative_to(local.ROOT / "exercises"))
        for p in (local.ROOT / "exercises").glob("*/*/solution.py")
    )


class Cgroup:
    """Reads the cgroup of a container from the host."""

    def __init__(self, container: local.Container):
        cid = local.docker("inspect", "--format", "{{.Id}}", container.name)
        self.path = Path(f"/sys/fs/cgroup/system.slice/docker-{cid}.scope")
        self.anon_peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def read(self, name: str) -> str:
        return (self.path / name).read_text()

    def cpu_s(self) -> float:
        return int(self.read("cpu.stat").split()[1]) / 1e6

    def peak_mb(self) -> float:
        return int(self.read("memory.peak")) / MIB

    def _sample(self) -> None:
        while not self._stop.is_set():
            try:
                stat = dict(line.split() for line in self.read("memory.stat").splitlines())
                used = sum(int(stat[k]) for k in ("anon", "shmem", "kernel"))
                self.anon_peak = max(self.anon_peak, used)
            except OSError:
                return
            time.sleep(0.01)

    def watch(self) -> None:
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        self._thread.join()


def post(url: str, body: dict[str, str]) -> tuple[float, dict[str, Any]]:
    req = urllib.request.Request(
        f"{url}/run", json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    return (time.monotonic() - start) * 1000, out


def measure(exercise: str, type_: str, warm: int, runtime: str) -> dict[str, Any]:
    cpus, memory = TYPES[type_]
    code = (local.ROOT / "exercises" / exercise / "solution.py").read_text()
    body = {"mode": "check", "exercise": exercise, "code": code}
    t0 = time.monotonic()
    container = local.start(runtime=runtime, cpus=cpus, memory=memory)
    started_ms = (time.monotonic() - t0) * 1000
    cgroup = Cgroup(container)
    cgroup.watch()
    runs = []
    try:
        baseline_mb = cgroup.peak_mb()
        for n in range(warm + 1):
            cpu0 = cgroup.cpu_s()
            ms, out = post(container.url, body)
            runs.append(
                {
                    "cold": n == 0,
                    "latency_ms": round(ms),
                    "runner_ms": out["ms"],
                    "peak_mb": out["peak_mb"],
                    "cpu_s": round(cgroup.cpu_s() - cpu0, 3),
                    "passed": out["passed"],
                    "killed": out["killed"],
                    "error": out["error"],
                }
            )
        record = {
            "exercise": exercise,
            "type": type_,
            "start_ms": round(started_ms),
            "baseline_mb": round(baseline_mb),
            "memory_peak_mb": round(cgroup.peak_mb()),
            "memory_anon_mb": round(cgroup.anon_peak / MIB),
            "runs": runs,
        }
    finally:
        cgroup.close()
        container.stop()
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--types", nargs="+", choices=TYPES, default=["standard-2"])
    parser.add_argument("--exercises", nargs="+", default=None)
    parser.add_argument("--warm", type=int, default=1)
    parser.add_argument("--runtime", choices=("runc", "runsc"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime or local.default_runtime()
    records = []
    for exercise in args.exercises or solutions():
        for type_ in args.types:
            records.append(measure(exercise, type_, args.warm, runtime))
            args.out.write_text(json.dumps(records, indent=1))
            print(f"done {exercise} {type_}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
