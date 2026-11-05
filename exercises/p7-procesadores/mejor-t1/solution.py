def mejor_t1(backend):
    return max(
        range(backend.num_qubits),
        key=lambda qubit: backend.qubit_properties(qubit).t1,
    )
