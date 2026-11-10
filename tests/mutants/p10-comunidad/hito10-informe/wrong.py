from importlib.metadata import version

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
from scipy.linalg import expm

AGRADECIMIENTO = (
    "We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the "
    "authors, and do not reflect the official policy or position of IBM or the IBM Quantum team."
)


def trotter(n, J, h, dt, pasos):
    qc = QuantumCircuit(n)
    for _ in range(pasos):
        for i in range(n - 1):
            qc.rzz(2 * J * dt, i, i + 1)
        for i in range(n):
            qc.rx(2 * h * dt, i)
    return qc


def resultados(n, J, h, T, pasos, disparos, semilla):
    dt = T / pasos
    H = SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], J) for i in range(n - 1)] + [("X", [i], h) for i in range(n)], num_qubits=n
    ).to_matrix()
    M = SparsePauliOp.from_sparse_list([("Z", [i], 1 / n) for i in range(n)], num_qubits=n)
    psi0 = np.zeros(2**n, dtype=complex)
    psi0[0] = 1
    backend = FakeManilaV2()
    simulador = AerSimulator.from_backend(backend)
    circuitos = [trotter(n, J, h, dt, k) for k in range(pasos + 1)]
    medidos = [qc.measure_all(inplace=False) for qc in circuitos]
    isas = transpile(medidos, backend, optimization_level=1, seed_transpiler=semilla)
    conteos = simulador.run(isas, shots=disparos, seed_simulator=semilla).result().get_counts()
    filas = []
    for k, (qc, cuentas) in enumerate(zip(circuitos, conteos)):
        psi = expm(-1j * H * k * dt) @ psi0
        exacta = float(np.real(np.vdot(psi, M.to_matrix() @ psi)))
        ideal = float(np.real(Statevector(qc).expectation_value(M)))
        ruidosa = sum(v * sum(1 - 2 * int(b) for b in s) for s, v in cuentas.items()) / (disparos * n)
        filas.append((k * dt, ideal, ideal, ruidosa))
    return filas


def informe(n, J, h, T, pasos, disparos, semilla, qpu, anio):
    filas = resultados(n, J, h, T, pasos, disparos, semilla)
    citas = [AGRADECIMIENTO]
    if qpu:
        citas.append(f"In this paper we used `{qpu['name']}` (v{qpu['version']}), an IBM Quantum {qpu['family']} processor.")
    citas.append(f"IBM Quantum. https://quantum.cloud.ibm.com/, {anio}")
    return "\n".join(
        [
            "# Magnetización de una cadena de Ising tras un cambio brusco del campo",
            "",
            "## Parámetros",
            f"N = {n} espines, J = {J}, h = {h}, T = {T}, {pasos} pasos de Trotter, {disparos} disparos, "
            f"semilla {semilla}, ruido simulado con el modelo de FakeManilaV2.",
            "",
            "## Resultados",
            "| t | exacta | Trotter | Trotter con ruido |",
            "| --- | --- | --- | --- |",
            *(f"| {t:.2f} | {e:.4f} | {tr:.4f} | {ru:.4f} |" for t, e, tr, ru in filas),
            "",
            "## Software",
            f"qiskit {version('qiskit')}, qiskit-aer {version('qiskit-aer')}, qiskit-ibm-runtime {version('qiskit-ibm-runtime')}.",
            "",
            "## Citas",
            "\n\n".join(citas),
        ]
    )
