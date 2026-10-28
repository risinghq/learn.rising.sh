import math


def periodo(theta0, dt=0.001):
    theta, omega, t = theta0, 0.0, 0.0
    while True:
        omega -= 0.5 * dt * math.sin(theta)
        nuevo = theta + dt * omega
        omega -= 0.5 * dt * math.sin(nuevo)
        t += dt
        if nuevo <= 0:
            cruce = t - dt + dt * theta / (theta - nuevo)
            return 4 * cruce
        theta = nuevo


print(periodo(0.5))
