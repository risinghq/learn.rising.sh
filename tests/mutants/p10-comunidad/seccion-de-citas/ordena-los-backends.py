AGRADECIMIENTO = (
    "We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the "
    "authors, and do not reflect the official policy or position of IBM or the IBM Quantum team."
)


def cita_qpu(backend):
    familia = backend.processor_type["family"]
    return f"In this paper we used `{backend.name}` (v{backend.backend_version}), an IBM Quantum {familia} processor."


def seccion_de_citas(backends, anio):
    lineas = [AGRADECIMIENTO]
    lineas += [cita_qpu(backend) for backend in sorted(backends, key=lambda b: b.name)]
    lineas.append(f"IBM Quantum. https://quantum.cloud.ibm.com/, {anio}")
    return "\n".join(lineas)
