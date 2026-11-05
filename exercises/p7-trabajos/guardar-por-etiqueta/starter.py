import json
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit_ibm_runtime import RuntimeDecoder, RuntimeEncoder


class Trabajo:
    def __init__(self, job_id, seed, tags):
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()
        self._id = job_id
        self.tags = tags
        self._resultado = StatevectorSampler(seed=seed).run([qc]).result()

    def job_id(self):
        return self._id

    def result(self):
        return self._resultado


class Servicio:
    def __init__(self):
        self._trabajos = [
            Trabajo("job-1", 1, ["a", "b"]),
            Trabajo("job-2", 2, ["a"]),
            Trabajo("job-3", 3, ["b"]),
        ]

    def jobs(self, job_tags=()):
        return [t for t in self._trabajos if set(job_tags) <= set(t.tags)]


def guardar_por_etiqueta(servicio, etiquetas, carpeta):
    return []


def cargar(carpeta, job_id):
    return None
