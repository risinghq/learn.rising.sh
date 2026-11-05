def mejor_t1(backend):
    candidato = max(
        range(backend.num_qubits),
        key=lambda qubit: backend.qubit_properties(qubit).t1,
    )
    return 0
