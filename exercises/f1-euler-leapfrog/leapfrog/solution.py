def leapfrog(x, v, dt, pasos):
    for _ in range(pasos):
        v -= 0.5 * dt * x
        x += dt * v
        v -= 0.5 * dt * x
    return x, v


print(leapfrog(1.0, 0.0, 0.1, 1))
