def pesos_pec(lam):
    a, b = 1.0, 0.0  # ✏️ resuelve las dos ecuaciones
    return a, b


a, b = pesos_pec(0.05)
gamma = abs(a) + 3 * abs(b)
print(f"con lam = 0.05: a = {a:.4f}, b = {b:.4f}, γ = {gamma:.4f}")
