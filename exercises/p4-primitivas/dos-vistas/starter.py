from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp

bell = QuantumCircuit(2)
bell.h(0)
bell.cx(0, 1)

observables = [SparsePauliOp(p) for p in ["ZZ", "ZI", "XX"]]
evs = StatevectorEstimator().run([(bell, observables)]).result()[0].data.evs

prediccion = None   # ✏️ tu apuesta: una lista con ⟨ZZ⟩, ⟨ZI⟩ y ⟨XX⟩

bell_medido = bell.copy()
bell_medido.measure_all()
conteos_bell = StatevectorSampler(seed=3).run([bell_medido], shots=1024).result()[0].data.meas.get_counts()
# compruébalo con print(evs.round(3)) y print(conteos_bell)
