from qgcheck import inside, learner, visible


@inside
def cuenta(shape, shots):
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.circuit import Parameter
    from qiskit.primitives.containers.sampler_pub import SamplerPub

    qc = QuantumCircuit(1)
    qc.rx(Parameter("theta"), 0)
    pub = SamplerPub.coerce((qc, np.zeros(shape)), shots=shots)
    return learner.ejecuciones(pub)


@visible("cuatro circuitos por 2000 disparos")
def test_broadcasting():
    got = cuenta((4, 1), 2000)
    assert got == 8000, f"Con shape = (4, 1) y shots = 2000, devuelve {got}."


def test_two_dimensions():
    got = cuenta((2, 3), 100)
    assert got == 600, f"Con shape = (2, 3) y shots = 100, devuelve {got}."
