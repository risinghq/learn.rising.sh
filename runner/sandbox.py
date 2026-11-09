"""Run a learner's job under limits and return what it produced.

The calling process runs as root. Each job gets the uid of its slot (`slot_uid`), a new
working directory and the limits of `launcher.py`. This module watches the limits the kernel
does not enforce by itself: clock, total memory, directory size and output volume. When the job
ends, all processes of that uid are killed and its files are deleted, including those in
/scratch, /tmp, /var/tmp and /dev/shm.
"""

import contextlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from qgcheck.runner import REPORT_CAP, drain, job_env

APP = Path(__file__).resolve().parent
SCRATCH_ROOT = Path(os.environ.get("QG_SCRATCH", "/scratch"))
UID_BASE = 20000
SHARED_DIRS = ("/scratch", "/tmp", "/var/tmp", "/dev/shm")
PAGE = os.sysconf("SC_PAGE_SIZE")
POLL_S = 0.02
PEAK_POLL_S = 0.5
DISK_POLL_S = 0.1
MAX_ENTRIES = 5000


@dataclass(frozen=True)
class Limits:
    wall_s: float = 10.0
    mem_mb: int = 512
    # RLIMIT_DATA counts reserved address space: `import qiskit` alone reserves about 1.2 GB.
    data_mb: int = 2048
    scratch_mb: int = 64
    out_bytes: int = 64 * 1024
    nproc: int = 64
    file_mb: int = 16


@dataclass
class Outcome:
    output: str
    report: bytes
    killed: str | None
    peak_mb: int
    ms: int


def _pids_of(uid: int) -> Iterator[int]:
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            if os.stat(f"/proc/{name}").st_uid == uid:
                yield int(name)
        except OSError:
            continue


def _rss_bytes(uid: int) -> int:
    """Resident memory of the processes of `uid`.

    It is an upper bound of the PSS and lets us avoid the costly PSS read.
    """
    total = 0
    for pid in _pids_of(uid):
        try:
            with open(f"/proc/{pid}/statm") as f:
                total += int(f.read().split()[1]) * PAGE
        except OSError, ValueError, IndexError:
            continue
    return total


def _pss_bytes(uid: int) -> int:
    """Proportional memory (PSS) of the processes of `uid`.

    A page shared among processes is split among them. The learner's process shares memory
    with the checker it forked from, and does not count it twice. Reading `smaps_rollup`
    across uids requires `CAP_SYS_PTRACE`; without it the read fails with `PermissionError`
    instead of counting zero.
    """
    total = 0
    for pid in _pids_of(uid):
        try:
            with open(f"/proc/{pid}/smaps_rollup") as f:
                for line in f:
                    if line.startswith("Pss:"):
                        total += int(line.split()[1]) * 1024
                        break
        except FileNotFoundError, ProcessLookupError:
            continue
    return total


def kill_uid(uid: int) -> None:
    """Kill all processes of `uid`, including those that called setsid."""
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        pids = list(_pids_of(uid))
        if not pids:
            return
        for pid in pids:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)
        time.sleep(0.01)


def _tree_bytes(root: Path) -> int | None:
    """Bytes on disk under `root`; None if there are too many entries."""
    total = 0
    seen = 0
    stack = [str(root)]
    while stack:
        try:
            with os.scandir(stack.pop()) as it:
                for e in it:
                    seen += 1
                    if seen > MAX_ENTRIES:
                        return None
                    st = e.stat(follow_symlinks=False)
                    total += st.st_blocks * 512
                    if e.is_dir(follow_symlinks=False):
                        stack.append(e.path)
        except OSError:
            continue
    return total


def _remove_owned(uid: int, root: str) -> None:
    """Delete from `root` what belongs to `uid`, without following links."""
    for dirpath, dirnames, filenames in os.walk(root, topdown=False, followlinks=False):
        for name in filenames + dirnames:
            path = os.path.join(dirpath, name)
            try:
                if os.lstat(path).st_uid != uid:
                    continue
                if os.path.isdir(path) and not os.path.islink(path):
                    os.rmdir(path)
                else:
                    os.unlink(path)
            except OSError:
                continue


class _Scan(threading.Thread):
    """Watch memory and disk in its own thread.

    Walking /proc can take seconds while a fork bomb creates processes; this way the
    clock of `run_job` keeps running. `killed` is written before `tripped`.
    """

    def __init__(self, uid: int, work: Path, limits: Limits) -> None:
        super().__init__(daemon=True)
        self.uid, self.work = uid, work
        self.mem_cap = limits.mem_mb * 2**20
        self.disk_cap = limits.scratch_mb * 2**20
        self.peak = 0
        self.killed: str | None = None
        self.tripped = threading.Event()
        self.stopped = threading.Event()

    def run(self) -> None:
        next_disk = next_peak = 0.0
        while not self.stopped.wait(POLL_S):
            try:
                reason, next_disk, next_peak = self._pass(next_disk, next_peak)
            except Exception:
                # Without watching there are no limits. The job is killed, not left running.
                traceback.print_exc()
                reason = "scan"
            if reason:
                self.killed = reason
                self.tripped.set()
                return

    def _pass(self, next_disk: float, next_peak: float) -> tuple[str | None, float, float]:
        """One watch pass: return the reason for the kill and the next due times.

        The PSS never exceeds the RSS, so while the RSS fits under the cap the job
        cannot exceed it and the RSS is enough. The PSS is read when the RSS passes
        the cap, to decide, and every `PEAK_POLL_S`, to record the peak.
        """
        now = time.monotonic()
        if _rss_bytes(self.uid) > self.mem_cap or now >= next_peak:
            pss = _pss_bytes(self.uid)
            next_peak = time.monotonic() + PEAK_POLL_S
            self.peak = max(self.peak, pss)
            if pss > self.mem_cap:
                return "memory", next_disk, next_peak
        if now >= next_disk:
            next_disk = time.monotonic() + DISK_POLL_S
            used = _tree_bytes(self.work)
            if used is None or used > self.disk_cap:
                return "disk", next_disk, next_peak
        return None, next_disk, next_peak


def slot_uid(slot: int) -> int:
    return UID_BASE + slot


def run_job(
    slot: int,
    files: Mapping[str, str],
    argv: Sequence[str],
    limits: Limits,
    env: Mapping[str, str],
    report: bool = False,
) -> Outcome:
    """Run `argv` with `files` written to a new directory.

    `argv` and the values of `env` may use `{dir}`, the path of the directory.
    With `report=True` the child inherits a pipe, whose number goes in QG_REPORT_FD.
    Standard output and standard error go together, in the order they were written.
    `killed` is `time`, `memory`, `disk` or `output` if the job passed that limit,
    or `scan` if the watch failed and the job was killed without being measured.
    """
    uid = slot_uid(slot)
    start = time.monotonic()
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(dir=SCRATCH_ROOT))
    try:
        os.chown(work, uid, uid)
        os.chmod(work, 0o700)
        for name, text in files.items():
            path = work / name
            path.write_text(text, encoding="utf-8")
            os.chown(path, uid, uid)

        child_env = {
            **job_env(str(work), "/usr/local/bin:/usr/bin:/bin"),
            **{k: v.replace("{dir}", str(work)) for k, v in env.items()},
        }
        cmd = [a.replace("{dir}", str(work)) for a in argv]
        launch = [
            sys.executable,
            "-S",
            str(APP / "launcher.py"),
            str(uid),
            str(int(limits.wall_s) + 2),
            str(limits.data_mb * 2**20),
            str(limits.file_mb * 2**20),
            str(limits.nproc),
            "--",
            *cmd,
        ]
        pass_fds: tuple[int, ...] = ()
        rep_r = rep_w = None
        if report:
            rep_r, rep_w = os.pipe()
            child_env["QG_REPORT_FD"] = str(rep_w)
            pass_fds = (rep_w,)

        proc = subprocess.Popen(
            launch,
            cwd=work,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            pass_fds=pass_fds,
        )
        if rep_w is not None:
            os.close(rep_w)
        assert proc.stdout is not None

        over = threading.Event()
        out, rep = bytearray(), bytearray()
        readers = [
            threading.Thread(
                target=drain, args=(proc.stdout.fileno(), limits.out_bytes, out, over)
            ),
        ]
        if rep_r is not None:
            readers.append(threading.Thread(target=drain, args=(rep_r, REPORT_CAP, rep, over)))
        for t in readers:
            t.start()

        scan = _Scan(uid, work, limits)
        scan.start()
        killed: str | None = None
        deadline = start + limits.wall_s
        while proc.poll() is None:
            if over.is_set():
                killed = "output"
            elif scan.tripped.is_set():
                killed = scan.killed
            elif time.monotonic() > deadline:
                killed = "time"
            if killed:
                break
            time.sleep(POLL_S)

        with contextlib.suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        scan.stopped.set()
        kill_uid(uid)
        scan.join(timeout=2)
        for t in readers:
            t.join(timeout=2)
        proc.stdout.close()
        if rep_r is not None:
            os.close(rep_r)
        return Outcome(
            output=out.decode("utf-8", "replace"),
            report=bytes(rep),
            killed=killed,
            peak_mb=round(scan.peak / 2**20),
            ms=round((time.monotonic() - start) * 1000),
        )
    finally:
        kill_uid(uid)
        shutil.rmtree(work, ignore_errors=True)
        for d in SHARED_DIRS:
            _remove_owned(uid, d)
