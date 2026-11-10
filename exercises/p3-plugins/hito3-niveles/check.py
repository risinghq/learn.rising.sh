from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import learner, visible


def cadena(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def referencia(n, J, h, dt, pasos):
    qc = cadena(n, J, h, dt, pasos)
    fez = FakeFez()
    return {
        str(nivel): generate_preset_pass_manager(nivel, backend=fez, seed_transpiler=1).run(qc).depth()
        for nivel in range(4)
    }


@visible("6 espines y 4 pasos: una profundidad por nivel, y el nivel 3 queda por debajo del 0")
def test_seis_espines():
    got = learner.profundidades(6, 1.0, 0.5, 0.1, 4)
    assert isinstance(got, dict) and sorted(got) == ["0", "1", "2", "3"], (
        f"`profundidades` devuelve las claves {sorted(got) if isinstance(got, dict) else got!r}; deben ser '0', '1', '2' y '3'."
    )
    want = referencia(6, 1.0, 0.5, 0.1, 4)
    assert got == want, f"Con n = 6, J = 1.0, h = 0.5, dt = 0.1 y pasos = 4, devuelves {got} y FakeFez da {want}."
    assert got["3"] < got["0"], f"El nivel 3 deja profundidad {got['3']} y el 0 deja {got['0']}."


def test_cuatro_espines():
    got = learner.profundidades(4, 0.8, 1.2, 0.2, 3)
    assert got == referencia(4, 0.8, 1.2, 0.2, 3), (
        f"Con n = 4, J = 0.8, h = 1.2, dt = 0.2 y pasos = 3, `profundidades` devuelve {got}."
    )
