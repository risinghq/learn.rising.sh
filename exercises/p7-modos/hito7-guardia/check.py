import math

from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import learner, visible


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for q in range(n - 1):
            qc.rzz(2 * J * dt, q, q + 1)
        for q in range(n):
            qc.rx(2 * h * dt, q)
    return qc


def uso(n, J, h, dt, pasos, disparos):
    """2 s más (rep_delay + reset + duración) × disparos por circuito, redondeado arriba en cada uno."""
    fez = FakeFez()
    pm = generate_preset_pass_manager(backend=fez, optimization_level=1, seed_transpiler=1)
    agenda = generate_preset_pass_manager(target=fez.target, optimization_level=0, scheduling_method="alap")
    espera = fez.target["reset"][(0,)].duration + fez.default_rep_delay
    total = 0
    for k in range(1, pasos + 1):
        total += math.ceil(2 + (agenda.run(pm.run(cadena(n, J, h, dt, k))).estimate_duration(fez.target, unit="s") + espera) * disparos)
    return total


def leer(*args):
    got = learner.guardia(*args)
    assert isinstance(got, (list, tuple)) and len(got) == 2, f"`guardia` debe devolver (permitido, uso_s) y devuelve {got!r}."
    return bool(got[0]), got[1]


@visible("4 espines, 4 circuitos y 4096 disparos en FakeFez: el uso estimado y el permiso")
def test_cuatro_circuitos():
    permitido, got = leer(4, 1.0, 0.5, 0.1, 4, 4096, 540, True)
    assert got == uso(4, 1.0, 0.5, 0.1, 4, 4096), (
        f"Tu uso estimado es {got!r} s para 4 circuitos de 4096 disparos. Cada circuito suma 2 s más "
        "(rep_delay + reset + su duración) × disparos, redondeado arriba por separado."
    )
    assert permitido, f"Con activado = True y 540 s restantes, `guardia` no permite un uso de {got!r} s."
    apagado, _ = leer(4, 1.0, 0.5, 0.1, 4, 4096, 540, False)
    assert not apagado, "Con activado = False, `guardia` permite el envío."


def test_sin_presupuesto():
    permitido, got = leer(3, 0.8, 1.2, 0.25, 3, 100000, 80, True)
    assert got == uso(3, 0.8, 1.2, 0.25, 3, 100000) and not permitido, (
        f"Con n = 3, J = 0.8, h = 1.2, dt = 0.25, pasos = 3, disparos = 100000 y restante_s = 80, "
        f"`guardia` devuelve ({permitido!r}, {got!r})."
    )
