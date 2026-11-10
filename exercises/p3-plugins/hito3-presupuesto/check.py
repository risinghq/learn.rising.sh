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


# The level-3 depth differs by one across machines: messages omit it and budgets sit off a step's depth.
def profundidad(n, J, h, dt, pasos):
    pm = generate_preset_pass_manager(3, backend=FakeFez(), seed_transpiler=1)
    return pm.run(cadena(n, J, h, dt, pasos)).depth()


def cabe_justo(n, J, h, dt, presupuesto, pasos):
    """pasos cabe en el presupuesto y pasos + 1 ya no."""
    if not isinstance(pasos, int) or not 1 <= pasos <= 10:
        return False
    return profundidad(n, J, h, dt, pasos) <= presupuesto and (
        pasos == 10 or profundidad(n, J, h, dt, pasos + 1) > presupuesto
    )


@visible("6 espines con presupuesto 100: el último número de pasos que FakeFez deja por debajo de 100")
def test_seis_espines():
    got = learner.pasos_max(6, 1.0, 0.5, 0.1, 100)
    assert isinstance(got, int) and 1 <= got <= 10, f"`pasos_max` devuelve {got!r}; debe ser un entero de 1 a 10."
    assert profundidad(6, 1.0, 0.5, 0.1, got) <= 100, (
        f"Con {got} pasos, el circuito transpilado para FakeFez pasa del presupuesto de 100. "
        "Mide la profundidad después de transpilar."
    )
    assert cabe_justo(6, 1.0, 0.5, 0.1, 100, got), f"Con {got + 1} pasos la profundidad todavía cabe en 100."


def test_cuatro_espines():
    got = learner.pasos_max(4, 0.8, 1.2, 0.2, 68)
    assert cabe_justo(4, 0.8, 1.2, 0.2, 68, got), (
        f"Con n = 4, J = 0.8, h = 1.2, dt = 0.2 y presupuesto = 68, `pasos_max` devuelve {got!r}."
    )
