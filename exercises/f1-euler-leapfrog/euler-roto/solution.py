def euler(x, v, dt, pasos):
    for _ in range(pasos):
        x, v = x + dt * v, v - dt * x
    return x, v


print(euler(1.0, 0.0, 0.1, 100))
