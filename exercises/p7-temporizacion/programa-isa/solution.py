def programacion(isa, backend):
    filas = []
    for inst, inicio in zip(isa.data, isa.op_start_times, strict=True):
        op = inst.operation
        qubits = tuple(isa.find_bit(q).index for q in inst.qubits)
        if op.name == "delay":
            duracion = op.duration
        else:
            duracion = backend.target[op.name][qubits].duration / backend.dt
        filas.append((op.name, qubits, inicio, duracion))
    return filas
