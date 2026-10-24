"""Prueba el corredor por HTTP contra la imagen real en Docker.

    uv run pytest tests/runner_test.py

Construye `qg-runner` con `runner/local.py`. Se salta si Docker no responde.
`QG_DOCKER` y `QG_RUNTIME` eligen el comando y el runtime.
"""

import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "runner")]
import local  # noqa: E402

from qgcheck import grade, spec  # noqa: E402
from qgcheck.runner import parse_report  # noqa: E402

EXERCISES = ROOT / "exercises"
EXERCISE_IDS = spec.all_ids()


@pytest.fixture(scope="module")
def runner() -> Iterator[local.Container]:
    try:
        local.docker("info")
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"Docker no responde: {e}")
    local.build()
    container = local.start()
    yield container
    container.stop()


def post(
    container: local.Container, body: dict[str, Any], raw: bytes | None = None
) -> tuple[int, dict[str, Any]]:
    data = raw if raw is not None else json.dumps(body).encode()
    req = urllib.request.Request(f"{container.url}/run", data, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def run(container: local.Container, code: str) -> dict[str, Any]:
    status, out = post(container, {"code": code})
    assert status == 200, out
    return out


def check(container: local.Container, exercise: str, code: str) -> dict[str, Any]:
    status, out = post(container, {"mode": "check", "exercise": exercise, "code": code})
    assert status == 200, out
    return out


def health(container: local.Container) -> int:
    with urllib.request.urlopen(f"{container.url}/health", timeout=5) as r:
        return int(r.status)


def processes(container: local.Container) -> list[str]:
    out = run(container, "import os; print(*[p for p in os.listdir('/proc') if p.isdigit()])")
    return str(out["stdout"]).split()


def test_report_keeps_only_a_valid_hint_number() -> None:
    """El informe proviene del código del alumno, así que valida la pista."""
    cases = [{"name": "a", "hint": hint} for hint in (2, 0, True, "1", None)] + [{"name": "b"}]
    report = parse_report(json.dumps({"error": None, "tests": cases}).encode())
    assert report is not None
    _, tests = report
    assert [t["hint"] for t in tests] == [2, None, None, None, None, None]


def test_slot_is_free_before_the_client_hears_the_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quien recibe el resultado y envía otra petición no ve la ranura ocupada."""
    import server

    jobs = server.FREE_SLOTS.qsize()
    free_at_reply: list[int] = []
    reply = server.Handler.reply

    def spy(self: server.Handler, status: int, payload: dict[str, Any]) -> None:
        free_at_reply.append(server.FREE_SLOTS.qsize())
        reply(self, status, payload)

    monkeypatch.setattr(server, "execute", lambda *_: {"passed": True})
    monkeypatch.setattr(server.Handler, "reply", spy)
    http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{http.server_address[1]}/run",
            json.dumps({"code": "print(1)"}).encode(),
            {"Content-Type": "application/json"},
        )
        assert urllib.request.urlopen(request, timeout=5).status == 200
    finally:
        http.shutdown()
        http.server_close()
    assert free_at_reply == [jobs]


def test_run_returns_the_output_of_both_streams(runner: local.Container) -> None:
    out = run(runner, "import sys\nprint('hola')\nprint('aviso', file=sys.stderr)")
    assert out["passed"] is True
    assert out["stdout"] == "hola\naviso\n"
    assert out["error"] is None
    assert out["killed"] is None
    assert out["tests"] == []
    assert out["ms"] > 0


def test_run_reports_the_error_with_its_line(runner: local.Container) -> None:
    out = run(runner, "def f():\n    return 1 / 0\nf()")
    assert out["passed"] is False
    assert out["error"] == "ZeroDivisionError: division by zero (línea 2: return 1 / 0)"


def test_image_has_qiskit_aer_and_runtime(runner: local.Container) -> None:
    out = run(
        runner,
        "import qiskit, qiskit_aer, qiskit_ibm_runtime\n"
        "from qiskit_aer import AerSimulator\nprint(qiskit.__version__)",
    )
    assert out["passed"], out
    assert out["stdout"].strip() == "2.5.2"


@pytest.mark.parametrize("exercise", EXERCISE_IDS)
def test_check_passes_the_solution(runner: local.Container, exercise: str) -> None:
    out = check(runner, exercise, (EXERCISES / exercise / "solution.py").read_text())
    assert out["passed"], out
    assert out["tests"] and all(t["passed"] for t in out["tests"])


@pytest.mark.parametrize("exercise", EXERCISE_IDS)
@pytest.mark.parametrize("file", ["solution.py", "starter.py"])
def test_check_gives_the_result_of_qgcheck_grade(
    runner: local.Container, exercise: str, file: str
) -> None:
    code = (EXERCISES / exercise / file).read_text()
    local_result = grade(exercise, code)
    out = check(runner, exercise, code)
    assert {k: out[k] for k in ("passed", "stdout", "error", "tests")} == {
        k: local_result[k] for k in ("passed", "stdout", "error", "tests")
    }


@pytest.mark.parametrize("exercise", EXERCISE_IDS)
def test_check_fails_the_starter_with_messages(runner: local.Container, exercise: str) -> None:
    out = check(runner, exercise, (EXERCISES / exercise / "starter.py").read_text())
    assert out["passed"] is False
    failed = [t for t in out["tests"] if not t["passed"]]
    assert failed and all(t["message"] for t in failed)


def test_check_names_hidden_cases_by_number(runner: local.Container) -> None:
    out = check(
        runner,
        "p1-quickstart/ghz",
        "from qiskit import QuantumCircuit\n"
        "def ghz(n):\n    qc = QuantumCircuit(n)\n    qc.measure_all()\n    return qc\n",
    )
    by_name = {t["name"]: t for t in out["tests"]}
    assert by_name["n = 2, 3 y 4"]["visible"] is True
    assert by_name["n = 2, 3 y 4"]["message"].startswith("Con n = 2 salen ['00']")
    assert by_name["caso oculto 1"]["visible"] is False


def test_check_names_the_missing_function(runner: local.Container) -> None:
    out = check(runner, "p1-quickstart/ghz", "x = 1\n")
    assert out["passed"] is False
    assert out["tests"] and all("Falta definir `ghz`" in t["message"] for t in out["tests"])


def test_check_reports_an_exception_of_the_function(runner: local.Container) -> None:
    out = check(runner, "p1-quickstart/ghz", "def ghz(n):\n    return 1 / 0\n")
    assert out["passed"] is False
    assert out["tests"] and all(
        t["message"].startswith("Tu código lanzó ZeroDivisionError: division by zero")
        for t in out["tests"]
    )


def test_check_survives_a_syntax_error(runner: local.Container) -> None:
    out = check(runner, "p1-quickstart/ghz", "def ghz(n:\n")
    assert out["passed"] is False
    assert out["tests"] == []
    assert out["error"].startswith("SyntaxError") and "línea 1" in out["error"]


def test_check_returns_what_the_code_prints_once(runner: local.Container) -> None:
    code = (EXERCISES / "p1-quickstart/ghz/solution.py").read_text() + "\nprint('cargado')\n"
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["passed"] and out["stdout"].count("cargado") == 1


def failed_everything(out: dict[str, Any]) -> bool:
    return (
        out["passed"] is False
        and (out["error"] or out["tests"])
        and not any(t["passed"] for t in out["tests"])
    )


def test_check_cannot_pass_by_exiting_early(runner: local.Container) -> None:
    assert failed_everything(check(runner, "p1-quickstart/ghz", "import os\nos._exit(0)\n"))


GOOD_GHZ = """
from qiskit import QuantumCircuit
def good(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc
"""


def test_check_grades_the_submitted_function_not_a_replaced_one(runner: local.Container) -> None:
    code = (
        GOOD_GHZ
        + """
import qgcheck
qgcheck.learner.ghz = good
def ghz(n):
    qc = QuantumCircuit(n)
    qc.measure_all()
    return qc
"""
    )
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["passed"] is False
    assert not {t["name"]: t for t in out["tests"]}["n = 2, 3 y 4"]["passed"]


def test_check_cannot_be_passed_by_replacing_the_checker(runner: local.Container) -> None:
    code = """
import builtins, qgcheck, sys
qgcheck.learner.ghz = lambda n: None
qgcheck.counts = lambda *a, **k: {"0": 1}
sys.modules["qgcheck"] = None
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_cannot_pass_by_forging_the_report(runner: local.Container) -> None:
    code = """
import os
forged = b'{"error": null, "tests": [{"name": null, "visible": false, "passed": true, "message": null}]}'
for fd in range(3, 64):
    try:
        os.write(fd, forged)
    except OSError:
        pass
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_cannot_pass_by_flooding_the_channel(runner: local.Container) -> None:
    code = "import os\nfor fd in range(3, 64):\n    try: os.write(fd, b'\\xff' * 100000)\n    except OSError: pass\n"
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_processes_are_out_of_reach_of_the_learner_code(runner: local.Container) -> None:
    code = (
        GOOD_GHZ
        + """
import ctypes, os
checker = os.getppid()
runner = int(open(f"/proc/{checker}/stat").read().split(")")[1].split()[1])
for pid in (checker, runner):
    for path, mode in ((f"/proc/{pid}/mem", "r+b"), (f"/proc/{pid}/environ", "rb")):
        try:
            open(path, mode).read(1)
            print("leido", path)
        except OSError:
            print("denegado")
    opened = []
    for n in range(3, 64):
        try:
            opened.append(open(f"/proc/{pid}/fd/{n}", "wb", buffering=0))
        except OSError:
            pass
    print("abiertos" if opened else "denegado")
    if ctypes.CDLL(None, use_errno=True).ptrace(16, pid, 0, 0) == 0:
        print("ptrace")
    else:
        print("denegado")
ghz = good
"""
    )
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["passed"], out
    assert out["stdout"] == "denegado\n" * 8


def test_check_learner_code_holds_only_its_own_reply_channel(runner: local.Container) -> None:
    code = (
        GOOD_GHZ
        + """
import os
def ghz(n):
    print(len([f for f in os.listdir("/proc/self/fd") if int(f) > 2]))
    return good(n)
"""
    )
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["passed"], out
    assert set(out["stdout"].split()) == {"2"}


def test_check_cannot_pass_by_prewriting_replies(runner: local.Container) -> None:
    code = """
import os
from qiskit import QuantumCircuit
from qgcheck.wire import encode, send
def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for k in range(n - 1):
        qc.cx(k, k + 1)
    qc.measure_all()
    return qc
replies = [{"ghz": True}] + [ghz(n) for n in (2, 5, 2, 3, 4, 5, 7, 5)]
for fd in range(255, 2, -1):
    for reply in replies:
        try:
            send(fd, {"value": encode(reply)})
        except Exception:
            pass
del ghz
"""
    assert failed_everything(check(runner, "p1-quickstart/ghz", code))


def test_check_does_not_import_what_the_learner_plants(runner: local.Container) -> None:
    code = (
        GOOD_GHZ
        + """
import os
for name in ("qiskit", "qiskit_aer", "numpy", "qgcheck", "json"):
    open(f"{name}.py", "w").write("print('PLANTADO')")
ghz = good
"""
    )
    out = check(runner, "p1-quickstart/ghz", code)
    assert out["passed"], out
    assert "PLANTADO" not in out["stdout"]


@pytest.mark.parametrize(
    "body, raw, status",
    [
        ({}, b"no es json", 400),
        ({"code": 5}, None, 400),
        ({"code": "x", "mode": "otro"}, None, 400),
        ({"code": "x", "mode": "check"}, None, 400),
        ({"code": "x", "mode": "check", "exercise": "../etc/passwd"}, None, 400),
        ({"code": "x", "mode": "check", "exercise": "p9-nada/nada"}, None, 404),
        ({"code": "x" * 20_001}, None, 413),
        ({"code": "x" * 130_000}, None, 413),
    ],
)
def test_rejects_bad_requests(
    runner: local.Container, body: dict[str, Any], raw: bytes | None, status: int
) -> None:
    got, out = post(runner, body, raw)
    assert got == status
    assert out["error"]


def test_accepts_code_whose_json_is_six_times_longer(runner: local.Container) -> None:
    tail = "\nprint('ok')\n"
    code = "# " + "\x01" * (20_000 - 2 - len(tail)) + tail
    assert len(code.encode()) == 20_000 and len(json.dumps({"code": code})) > 100_000
    assert run(runner, code)["stdout"] == "ok\n"


def test_unknown_path_is_404(runner: local.Container) -> None:
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(f"{runner.url}/nada", timeout=5)
    assert e.value.code == 404


def test_rejects_a_second_job_while_one_runs(runner: local.Container) -> None:
    first: dict[str, Any] = {}
    t = threading.Thread(
        target=lambda: first.update(out=run(runner, "import time; time.sleep(2); print('listo')"))
    )
    t.start()
    time.sleep(0.7)
    status, _ = post(runner, {"code": "print(1)"})
    t.join()
    assert status == 503
    assert first["out"]["stdout"] == "listo\n"


def test_timeout_kills_the_job(runner: local.Container) -> None:
    out = run(runner, "while True: pass")
    assert out["passed"] is False
    assert out["killed"] == "time"
    assert out["error"] == "Tu código tardó más de 10 s y se detuvo."
    assert 9_000 < out["ms"] < 13_000
    assert health(runner) == 200


@pytest.mark.parametrize(
    "code",
    [
        "x = bytearray(2 << 30)",
        "xs = []\nwhile True: xs.append(bytearray(50 << 20))",
        "import numpy as np\nx = np.ones((30000, 30000))",
    ],
)
def test_memory_cap(runner: local.Container, code: str) -> None:
    out = run(runner, code)
    assert out["passed"] is False
    assert out["killed"] == "memory" or out["error"].startswith("MemoryError")
    assert out["peak_mb"] < 700
    assert out["ms"] < 5_000
    assert health(runner) == 200


def test_job_is_killed_when_the_scan_cannot_read_memory() -> None:
    try:
        local.docker("info")
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"Docker no responde: {e}")
    blind = local.start(caps=tuple(c for c in local.CAPS if c != "SYS_PTRACE"))
    try:
        out = run(blind, "import time\ntime.sleep(8)\nprint('siguió')")
        assert out["killed"] == "scan"
        assert out["passed"] is False
        assert "no pudo vigilar" in out["error"]
        assert "siguió" not in out["stdout"]
        assert out["ms"] < 3_000
        assert health(blind) == 200
        again = run(blind, "import time\ntime.sleep(8)\nprint('siguió')")
        assert again["killed"] == "scan"
        assert "siguió" not in again["stdout"]
    finally:
        blind.stop()


def test_memory_cap_counts_every_process_of_the_job(runner: local.Container) -> None:
    out = run(
        runner,
        "import os, time\n"
        "for _ in range(2):\n"
        "    if os.fork() == 0:\n"
        "        x = bytearray(300 << 20)\n"
        "        x[::4096] = b'1' * len(x[::4096])\n"
        "        time.sleep(10)\n"
        "        os._exit(0)\n"
        "time.sleep(10)\n",
    )
    assert out["killed"] == "memory"
    assert out["peak_mb"] < 700
    assert out["ms"] < 5_000
    assert health(runner) == 200


def test_peak_counts_a_page_shared_with_a_forked_process_once(runner: local.Container) -> None:
    out = run(
        runner,
        "import os, time\n"
        "x = bytearray(200 << 20)\n"
        "x[::4096] = b'1' * len(x[::4096])\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    time.sleep(1)\n"
        "    os._exit(0)\n"
        "time.sleep(0.5)\n"
        "os.waitpid(pid, 0)\n",
    )
    assert out["passed"], out
    assert 200 <= out["peak_mb"] < 300


def test_job_runs_without_privileges(runner: local.Container) -> None:
    out = run(
        runner,
        "import os\nprint(os.getuid())\nprint(os.getgroups())\n"
        "print([l for l in open('/proc/self/status') if l.startswith('CapEff')][0].split()[1])",
    )
    uid, groups, caps = out["stdout"].split("\n")[:3]
    assert (uid, groups, int(caps, 16)) == ("20000", "[]", 0)


NETWORK_CODE = """
import socket
for family, address in ((socket.AF_INET, ("1.1.1.1", 53)), (socket.AF_INET6, ("2606:4700:4700::1111", 53))):
    try:
        socket.socket(family).connect(address)
        print("conectó")
    except PermissionError:
        print("denegado")
"""


def test_no_network(runner: local.Container) -> None:
    out = run(runner, NETWORK_CODE)
    assert out["stdout"] == "denegado\ndenegado\n"


def test_no_network_even_when_the_container_has_internet() -> None:
    try:
        local.docker("info")
    except (OSError, subprocess.CalledProcessError) as e:
        pytest.skip(f"Docker no responde: {e}")
    container = local.start(egress=True)
    try:
        try:
            container.exec(
                "python",
                "-c",
                "import socket; socket.create_connection(('1.1.1.1', 53), timeout=3)",
            )
        except subprocess.CalledProcessError:
            pytest.skip("el anfitrión no tiene salida a internet; no hay con qué comparar")
        out = run(container, NETWORK_CODE)
        assert out["stdout"] == "denegado\ndenegado\n"
    finally:
        container.stop()


def test_fork_bomb_is_contained(runner: local.Container) -> None:
    before = len(processes(runner))
    out = run(runner, "import os\nwhile True: os.fork()")
    assert out["passed"] is False
    assert out["ms"] < 13_000
    assert health(runner) == 200
    assert len(processes(runner)) <= before


def test_fork_bomb_that_swallows_errors_is_contained(runner: local.Container) -> None:
    before = len(processes(runner))
    out = run(runner, "import os\nwhile True:\n    try: os.fork()\n    except OSError: pass")
    assert out["passed"] is False
    assert out["ms"] < 13_000
    assert health(runner) == 200
    assert len(processes(runner)) <= before


def test_detached_process_does_not_outlive_the_job(runner: local.Container) -> None:
    before = len(processes(runner))
    out = run(
        runner,
        "import os, time\nif os.fork() == 0:\n    os.setsid()\n    time.sleep(300)\n    os._exit(0)",
    )
    assert out["passed"] is True
    assert len(processes(runner)) <= before


@pytest.mark.parametrize(
    "path",
    [
        "/x",
        "/app/x",
        "/app/server.py",
        "/etc/x",
        "/usr/local/x",
        "/var/tmp/x",
        "/tmp/x",
        "/dev/shm/x",
        "/scratch/x",
        "/proc/x",
        "/root/x",
        "/home/x",
    ],
)
def test_writes_outside_the_work_directory_fail(runner: local.Container, path: str) -> None:
    out = run(runner, f"open({path!r}, 'w').write('x')")
    assert out["passed"] is False
    assert "Error" in out["error"]


def test_writes_to_the_work_directory_work_and_do_not_persist(runner: local.Container) -> None:
    out = run(
        runner, "import os\nopen('nota.txt', 'w').write('hola')\nprint(sorted(os.listdir('.')))"
    )
    assert out["stdout"] == "['main.py', 'nota.txt']\n"
    again = run(runner, "import os\nprint(sorted(os.listdir('.')))")
    assert again["stdout"] == "['main.py']\n"


def test_a_job_cannot_read_the_files_of_the_previous_one(runner: local.Container) -> None:
    run(runner, "open('secreto.txt', 'w').write('x')")
    out = run(runner, "import glob\nprint(glob.glob('/scratch/*/secreto.txt'))")
    assert out["stdout"] == "[]\n"


def test_disk_fill_is_stopped(runner: local.Container) -> None:
    out = run(runner, "for i in range(100):\n    open(f'f{i}', 'wb').write(b'x' * (8 << 20))")
    assert out["passed"] is False
    assert out["killed"] == "disk" or "No space left" in out["error"]
    assert out["ms"] < 5_000
    assert health(runner) == 200


def test_single_huge_file_is_refused(runner: local.Container) -> None:
    out = run(runner, "open('grande', 'wb').write(b'x' * (64 << 20))")
    assert out["passed"] is False
    assert "File too large" in out["error"]


def test_output_flood_is_cut(runner: local.Container) -> None:
    out = run(runner, "while True: print('x' * 1000)")
    assert out["passed"] is False
    assert out["killed"] == "output"
    assert len(out["stdout"]) <= 64 * 1024
