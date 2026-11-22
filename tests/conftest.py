import os
from pathlib import Path

import pytest


def cores() -> int:
    """The physical cores among the CPUs this process may run on."""
    try:
        return len(
            {
                Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/core_cpus_list").read_text()
                for cpu in os.sched_getaffinity(0)
            }
        )
    except AttributeError, OSError:
        return os.process_cpu_count() or 1


if workers := os.environ.get("PYTEST_XDIST_WORKER_COUNT"):
    threads = str(max(1, (os.process_cpu_count() or 1) // int(workers)))
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "RAYON_NUM_THREADS"):
        os.environ.setdefault(name, threads)


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    return cores()
