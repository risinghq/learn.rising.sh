import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector

from qgcheck import inside, learner, visible


def bell():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


def plus_zero():
    qc = QuantumCircuit(2)
    qc.h(0)
    return qc


def exact(circuit, labels):
    state = Statevector(circuit)
    return np.array([state.expectation_value(SparsePauliOp(label)).real for label in labels])


@inside
def bars(circuit, labels):
    axes = learner.graficar(circuit, labels)
    heights = [patch.get_height() for patch in axes.patches]
    names = [tick.get_text() for tick in axes.get_xticklabels()]
    return names, heights


@visible("Bell: ⟨ZZ⟩ = ⟨XX⟩ = 1, ⟨YY⟩ = −1 y los de un solo qubit valen 0")
def test_values():
    labels = ["ZZ", "XX", "YY", "ZI", "IZ"]
    got = np.asarray(learner.valores_esperados(bell(), labels), dtype=float)
    assert got.shape == (5,), f"El resultado tiene forma {got.shape} y debería ser un arreglo de 5 valores."
    assert np.allclose(got, exact(bell(), labels), atol=1e-6), f"Salen {np.round(got, 2).tolist()}; esperaba ZZ = 1, XX = 1, YY = −1, ZI = IZ = 0."


@visible("la gráfica tiene una barra por etiqueta, con su valor")
def test_bars():
    labels = ["ZZ", "XX", "YY", "ZI", "IZ"]
    names, heights = bars(bell(), labels)
    assert names == labels, f"Las barras se llaman {names}; deberían llamarse como las etiquetas."
    assert np.allclose(heights, exact(bell(), labels), atol=1e-6), f"Las barras miden {np.round(heights, 2).tolist()}; no son los valores esperados."


def test_other_circuit():
    labels = ["XI", "IX", "ZI", "ZZ"]
    got = np.asarray(learner.valores_esperados(plus_zero(), labels), dtype=float)
    ok = got.shape == (4,) and np.allclose(got, exact(plus_zero(), labels), atol=1e-6)
    assert ok, f"Con una H en el qubit 0 y las etiquetas {labels}, `valores_esperados` devuelve {np.round(got, 2).tolist()}."


def test_single_label():
    got = np.asarray(learner.valores_esperados(bell(), ["XX"]), dtype=float)
    assert got.shape == (1,) and np.allclose(got, [1], atol=1e-6), (
        f"Con la etiqueta ['XX'], `valores_esperados` devuelve un arreglo de forma {got.shape} con {np.round(got, 2).tolist()}.")


def test_bars_for_another_circuit():
    labels = ["XI", "ZI", "IZ"]
    names, heights = bars(plus_zero(), labels)
    ok = names == labels and np.allclose(heights, exact(plus_zero(), labels), atol=1e-6)
    assert ok, f"Con una H en el qubit 0 y las etiquetas {labels}, `graficar` dibuja barras llamadas {names} que miden {np.round(heights, 2).tolist()}."
