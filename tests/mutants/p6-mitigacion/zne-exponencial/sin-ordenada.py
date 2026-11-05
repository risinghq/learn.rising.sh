import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, SparsePauliOp
from qiskit_aer.noise import depolarizing_error


def plegar(qc, k):
    """Plegado global U (U† U)^k: misma operación ideal, factor de ruido 2k + 1."""
    out = qc.copy()
    for _ in range(k):
        out.compose(qc.inverse(), inplace=True)
        out.compose(qc, inplace=True)
    return out


def esperanza(qc, lam, obs):
    """Valor esperado exacto si cada CX sufre ruido despolarizante lam (matriz densidad)."""
    rho = DensityMatrix.from_label("0" * qc.num_qubits)
    canal = depolarizing_error(lam, 2).to_quantumchannel()
    for inst in qc.data:
        qubits = [qc.find_bit(q).index for q in inst.qubits]
        rho = rho.evolve(inst.operation, qubits)
        if inst.operation.name == "cx":
            rho = rho.evolve(canal, qubits)
    return float(rho.expectation_value(obs).real)


ghz = QuantumCircuit(4)
ghz.h(0)
for q in range(3):
    ghz.cx(q, q + 1)
observable = SparsePauliOp("ZIIZ")
lam = 0.02

factores = [1, 3, 5]
valores = [esperanza(plegar(ghz, (f - 1) // 2), lam, observable) for f in factores]


def extrapolar_exp(factores, valores):
    """Valor en el factor 0 de una exponencial E(c) = E0 · exp(-g · c) ajustada a los puntos."""
    x = np.array(factores, dtype=float)
    pendiente = np.sum(x * np.log(valores)) / np.sum(x * x)
    return float(np.exp(0 * pendiente))


zne_exp = extrapolar_exp(factores, valores)
print(f"sin mitigar: {valores[0]:.4f} · ZNE exponencial: {zne_exp:.4f} · ideal: 1")
