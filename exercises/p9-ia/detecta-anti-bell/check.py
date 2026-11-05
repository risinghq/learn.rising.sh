from qgcheck import learner, visible

CORRECTA = """
from qiskit import QuantumCircuit

def anti_bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.x(0)
    return qc
"""
VARIANTES = {
    "correcta": CORRECTA,
    "sin X": CORRECTA.replace("    qc.x(0)\n", ""),
    "con signo": CORRECTA.replace("    qc.x(0)\n", "    qc.x(0)\n    qc.z(0)\n"),
}


def veredicto(variante):
    return "acepta" if learner.es_anti_bell(VARIANTES[variante]) else "rechaza"


@visible("acepta la respuesta correcta")
def test_accepts_the_right_answer():
    variante = "correcta"
    got = veredicto(variante)
    assert got == "acepta", f"Con la variante {variante!r}, tu `es_anti_bell` {got} el código."


def test_rejects_the_missing_x():
    variante = "sin X"
    got = veredicto(variante)
    assert got == "rechaza", f"Con la variante {variante!r}, tu `es_anti_bell` {got} el código."


def test_rejects_the_minus_sign():
    variante = "con signo"
    got = veredicto(variante)
    assert got == "rechaza", f"Con la variante {variante!r}, tu `es_anti_bell` {got} el código."
