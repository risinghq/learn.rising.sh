from qiskit.quantum_info import PauliLindbladMap

modelo = PauliLindbladMap.from_list([("XI", 0.010), ("IZ", 0.005), ("ZZ", 0.002)])
gamma_capa = modelo.inverse().gamma()


def amplificar(modelo, factor):
    """El mismo modelo con todas sus tasas multiplicadas por `factor`."""
    nuevo = modelo.scale_rates(factor)
    globals()["modelo"] = nuevo
    return nuevo


amplificado = amplificar(modelo, 3)
print("tasas:", [round(float(r), 5) for r in amplificado.rates])
print(f"γ: {gamma_capa:.5f} → {amplificado.inverse().gamma():.5f} (γ³ = {gamma_capa**3:.5f})")
