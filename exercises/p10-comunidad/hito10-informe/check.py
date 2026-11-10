from importlib.metadata import version

import numpy as np
from scipy.linalg import expm

from qgcheck import learner, visible

X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1.0, -1.0]).astype(complex)


def sobre(n, ops):
    """El producto de Kronecker con ops[q] en el qubit q; Qiskit pone el qubit 0 a la derecha."""
    m = np.eye(1, dtype=complex)
    for q in reversed(range(n)):
        m = np.kron(m, ops.get(q, np.eye(2)))
    return m


def enlaces(n, J):
    return sum((J * sobre(n, {i: Z, i + 1: Z}) for i in range(n - 1)), np.zeros((2**n, 2**n)))


def campo(n, h):
    return sum(h * sobre(n, {i: X}) for i in range(n))


def magnetizacion(n):
    return sum(sobre(n, {i: Z}) for i in range(n)) / n


def ising(n, J, h):
    return enlaces(n, J) + campo(n, h)


def inicial(n):
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1
    return psi


def curva(n, U, pasos):
    psi, M, valores = inicial(n), magnetizacion(n), []
    for _ in range(pasos + 1):
        valores.append(float(np.real(np.vdot(psi, M @ psi))))
        psi = U @ psi
    return np.array(valores)


def exacta(n, J, h, dt, pasos):
    return curva(n, expm(-1j * dt * ising(n, J, h)), pasos)


def trotter(n, J, h, dt, pasos):
    return curva(n, expm(-1j * dt * campo(n, h)) @ expm(-1j * dt * enlaces(n, J)), pasos)

AGRADECIMIENTO = (
    "We acknowledge the use of IBM Quantum services for this work. The views expressed are those of the "
    "authors, and do not reflect the official policy or position of IBM or the IBM Quantum team."
)
QPU = {"name": "ibm_fez", "version": "1.2.8", "family": "Heron"}


def tabla(texto):
    filas = []
    for linea in texto.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")] if linea.startswith("|") else []
        try:
            filas.append([float(c) for c in celdas])
        except ValueError:
            continue
    return np.array([f for f in filas if len(f) == 4])


@visible("4 espines, T = 2, 8 pasos y un QPU: parámetros, tabla con las tres curvas, versiones y citas")
def test_con_qpu():
    texto = learner.informe(4, 1.0, 1.0, 2.0, 8, 4000, 7, QPU, 2026)
    assert isinstance(texto, str) and texto.startswith("# "), f"El informe debe empezar con un título `# ` y empieza {str(texto)[:30]!r}."
    sin_dato = [x for x in (4, 1.0, 2.0, 8, 4000, 7) if str(x) not in texto]
    assert not sin_dato, f"En los parámetros del informe faltan {sin_dato}: N, J, h, T, pasos, disparos y semilla."
    faltan = [p for p in ("qiskit", "qiskit-aer", "qiskit-ibm-runtime") if f"{p} {version(p)}" not in texto]
    assert not faltan, f"Al informe le faltan las versiones de {faltan}."
    filas = tabla(texto)
    assert filas.shape == (9, 4), f"Tu tabla tiene {len(filas)} filas de 4 números; con 8 pasos lleva una por instante, de t = 0 a t = T."
    assert np.allclose(filas[:, 0], np.linspace(0, 2, 9), atol=0.006), f"Tu columna t es {filas[:, 0].tolist()}."
    assert np.allclose(filas[:, 1], exacta(4, 1.0, 1.0, 0.25, 8), atol=6e-4), f"Tu columna exacta es {filas[:, 1].tolist()}."
    assert np.allclose(filas[:, 2], trotter(4, 1.0, 1.0, 0.25, 8), atol=6e-4), f"Tu columna Trotter es {filas[:, 2].tolist()}."
    ruido = np.abs(filas[:, 3] - filas[:, 2])
    assert ruido.max() < 0.2 and ruido.max() > 0.02, f"Tu columna con ruido es {filas[:, 3].tolist()}; simula con el ruido de FakeManilaV2."
    frase = "In this paper we used `ibm_fez` (v1.2.8), an IBM Quantum Heron processor."
    assert AGRADECIMIENTO in texto and frase in texto and "IBM Quantum. https://quantum.cloud.ibm.com/, 2026" in texto, (
        "Faltan citas: el agradecimiento, la frase del QPU y la referencia con el año."
    )


def test_sin_qpu():
    texto = learner.informe(3, 0.8, 1.2, 1.5, 3, 2000, 3, None, 2025)
    filas = tabla(texto)
    assert filas.shape == (4, 4) and np.allclose(filas[:, 1], exacta(3, 0.8, 1.2, 0.5, 3), atol=6e-4), (
        f"Con n = 3, J = 0.8, h = 1.2, T = 1.5, pasos = 3 y qpu = None, la columna exacta de `informe` es {filas[:, 1:2].ravel().tolist()}."
    )
    assert "In this paper we used" not in texto and "IBM Quantum. https://quantum.cloud.ibm.com/, 2025" in texto, (
        f"Con qpu = None y anio = 2025, las citas de `informe` son {texto.split('## Citas')[-1].strip()[:200]!r}."
    )
