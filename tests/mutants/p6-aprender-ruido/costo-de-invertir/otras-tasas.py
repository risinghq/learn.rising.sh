from qiskit.quantum_info import PauliLindbladMap, QubitSparsePauli

modelo = PauliLindbladMap.from_list([("XI", 0.020), ("IZ", 0.005), ("ZZ", 0.002)])
for etiqueta in ("ZZ", "XX", "IZ"):
    print(
        f"fidelidad de {etiqueta}:",
        round(modelo.pauli_fidelity(QubitSparsePauli.from_label(etiqueta)), 5),
    )

# ✏️ el coste γ de invertir una capa con este modelo
gamma_capa = modelo.inverse().gamma()
print("γ para invertir una capa:", round(gamma_capa, 5))

# ✏️ apuesta antes de mirar la línea de arriba: ¿γ será "menor que 1" o "mayor que 1"?
prediccion = "mayor que 1"
