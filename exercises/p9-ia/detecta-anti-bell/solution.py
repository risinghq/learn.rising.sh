def es_anti_bell(codigo):
    import numpy as np
    from qiskit.quantum_info import Statevector

    espacio = {}
    try:
        exec(codigo, espacio)
        estado = Statevector(espacio["anti_bell"]())
    except Exception:
        return False
    objetivo = Statevector(np.array([0, 1, 1, 0]) / np.sqrt(2))
    return bool(estado.equiv(objetivo))
