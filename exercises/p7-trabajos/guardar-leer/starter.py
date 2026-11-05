import json

from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit_ibm_runtime import RuntimeDecoder, RuntimeEncoder


def roundtrip(seed):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    resultado = StatevectorSampler(seed=seed).run([qc]).result()
    # Guarda resultado con RuntimeEncoder y vuelve a leerlo con RuntimeDecoder.
    return None
