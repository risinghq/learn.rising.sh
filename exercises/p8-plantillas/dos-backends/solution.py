import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer.primitives import EstimatorV2 as AerEstimator
from qiskit_ibm_runtime.fake_provider import FakeBelemV2


def comparar_backends(t_steps):
    circuitos = []
    for k in range(t_steps + 1):
        qc = QuantumCircuit(4)
        for _ in range(k):
            for qubit in range(0, 3, 2):
                qc.rzz(0.4, qubit, qubit + 1)
            for qubit in range(1, 3, 2):
                qc.rzz(0.4, qubit, qubit + 1)
            for qubit in range(4):
                qc.rx(0.2, qubit)
        circuitos.append(qc)
    observable = SparsePauliOp.from_sparse_list([("Z", [i], 0.25) for i in range(4)], num_qubits=4)
    exacto = StatevectorEstimator().run([(circuito, observable) for circuito in circuitos]).result()
    fake = FakeBelemV2()
    pm = generate_preset_pass_manager(1, backend=fake, seed_transpiler=1)
    pubs = []
    for circuito in circuitos:
        isa = pm.run(circuito)
        pubs.append((isa, observable.apply_layout(isa.layout)))
    ruidoso = (
        AerEstimator.from_backend(fake, options={"backend_options": {"seed_simulator": 3}})
        .run(pubs, precision=0.02)
        .result()
    )
    valores = [float(item.data.evs) for item in exacto]
    con_ruido = [float(item.data.evs) for item in ruidoso]
    return len(valores), valores[0], float(np.max(np.abs(np.array(valores) - con_ruido)))
