def propiedades(backend):
    medir = backend.target["measure"][(0,)].duration
    cz = backend.target["cz"][(0, 1)].duration
    return {
        "qubits": backend.num_qubits,
        "familia": backend.processor_type["family"],
        "razon": medir / cz,
    }
