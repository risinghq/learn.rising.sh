def cita_qpu(backend):
    familia = backend.processor_type["family"]
    return f"In this paper we used `{backend.name}` (v{backend.backend_version}), an IBM Quantum Heron processor."
