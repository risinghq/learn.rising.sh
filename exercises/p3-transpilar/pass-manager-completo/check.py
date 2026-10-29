import functools

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit_ibm_runtime.fake_provider import FakeFez

from qgcheck import inside, learner, operator, unsupported, visible


class FakeFezWithoutCalibration(FakeFez):
    # Same gates and coupling map as FakeFez; reading its calibration takes 0.1 s of CPU.
    props_filename = None


TARGET = FakeFezWithoutCalibration().target


@inside
def run_pass_manager(level, circuit):
    return learner.pass_manager(level).run(circuit)


# Each pass manager is built for the 156-qubit chip: the cases share their results.
@functools.cache
def isa_of(level, make):
    return run_pass_manager(level, make())


def toffoli():
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.ccx(0, 1, 2)
    return qc


def fredkin():
    qc = QuantumCircuit(3)
    qc.h(1)
    qc.cswap(0, 1, 2)
    return qc


def ghz4():
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, [1, 2, 3])
    return qc


@visible("el circuito sale ISA para FakeFez")
def test_isa():
    bad = unsupported(isa_of(1, toffoli), TARGET)
    assert not bad, f"Con nivel = 1 quedan instrucciones que FakeFez no ejecuta: {bad}."


@visible("el circuito sigue haciendo lo mismo")
def test_same_operator():
    isa = isa_of(1, toffoli)
    assert operator(isa).equiv(Operator(toffoli())), "El circuito transpilado ya no implementa el mismo operador."


def test_every_level_and_circuit_is_isa():
    for make in (fredkin, ghz4):
        for nivel in range(4):
            bad = unsupported(isa_of(nivel, make), TARGET)
            assert not bad, f"Con `{make.__name__}()` y nivel = {nivel} quedan instrucciones que FakeFez no ejecuta: {bad}."


def test_every_level_keeps_the_operator():
    for make in (fredkin, ghz4):
        for nivel in range(4):
            isa = isa_of(nivel, make)
            assert operator(isa).equiv(Operator(make())), (
                f"Con `{make.__name__}()` y nivel = {nivel} el operador cambió; el circuito tiene {dict(isa.count_ops())}.")
