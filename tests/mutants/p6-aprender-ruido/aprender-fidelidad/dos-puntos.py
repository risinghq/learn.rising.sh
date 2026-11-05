import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix, PauliLindbladMap, QubitSparsePauli, SparsePauliOp
from qiskit_aer.noise import depolarizing_error


def zz_tras(d, lam=0.03):
    """⟨ZZ⟩ exacto tras d capas (dos CX) con ruido despolarizante lam en cada CX."""
    rho = DensityMatrix.from_label("00")
    canal = depolarizing_error(lam, 2).to_quantumchannel()
    cx = QuantumCircuit(2)
    cx.cx(0, 1)
    for _ in range(2 * d):
        rho = rho.evolve(cx).evolve(canal)
    return float(rho.expectation_value(SparsePauliOp("ZZ")).real)


profundidades = [1, 2, 4, 8]
medidas = [zz_tras(d) for d in profundidades]
print("⟨ZZ⟩ para d = 1, 2, 4, 8:", [round(m, 4) for m in medidas])


def aprender_fidelidad(ds, valores):
    pendiente, _ = np.polyfit(ds[:2], np.log(valores[:2]), 1)
    return float(np.exp(pendiente))


f_aprendida = aprender_fidelidad(profundidades, medidas)
tasa = -np.log(f_aprendida) / 2
modelo_aprendido = PauliLindbladMap.from_list([("XI", tasa)])
fidelidad_zz = modelo_aprendido.pauli_fidelity(QubitSparsePauli.from_label("ZZ"))
print(f"f = {f_aprendida:.5f} · r = {tasa:.5f} · fidelidad de ZZ en el modelo: {fidelidad_zz:.5f}")
