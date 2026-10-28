def aceleracion(x, y):
    r3 = (x * x + y * y) ** 1.5
    return -x / r3, -y / r3


def orbita(x, y, vx, vy, dt, pasos):
    ax, ay = aceleracion(x, y)
    for _ in range(pasos):
        vx += 0.5 * dt * ax
        vy += 0.5 * dt * ay
        x += dt * vx
        y += dt * vy
        ax, ay = aceleracion(x, y)
        vx += 0.5 * dt * ax
        vy += 0.5 * dt * ay
    return x, y, vx, vy


print(orbita(1.0, 0.0, 0.0, 1.0, 0.01, 628))
