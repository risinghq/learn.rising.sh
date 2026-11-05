def es_anti_bell(codigo):
    from qiskit.quantum_info import Statevector

    espacio = {}
    try:
        exec(codigo, espacio)
        probs = Statevector(espacio["anti_bell"]()).probabilities_dict()
    except Exception:
        return False
    return {k: round(v, 3) for k, v in probs.items()} == {"01": 0.5, "10": 0.5}
