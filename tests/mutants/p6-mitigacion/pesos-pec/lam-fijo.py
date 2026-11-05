def pesos_pec(lam):
    s = 1 / 0.95
    b = (1 - s) / 4
    a = s + b
    return a, b


a, b = pesos_pec(0.05)
gamma = abs(a) + 3 * abs(b)
print(f"con lam = 0.05: a = {a:.4f}, b = {b:.4f}, γ = {gamma:.4f}")
