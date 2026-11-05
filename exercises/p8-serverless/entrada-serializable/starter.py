from qiskit_ibm_runtime.fake_provider import FakeFez


def argumentos(circuitos):
    backend_name = FakeFez()
    return {"circuits": circuitos, "backend_name": backend_name, "optimization_level": 3}
