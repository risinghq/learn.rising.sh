from qgcheck import learner, visible


@visible("fija la versión menor de 2.4.0")
def test_minor_of_240():
    version = "2.4.0"
    got = learner.restriccion(version)
    assert got == "qiskit~=2.4.0", f"Con version = {version!r}, `restriccion` devuelve {got!r}."


def test_patch_is_dropped():
    version = "2.5.3"
    got = learner.restriccion(version)
    assert got == "qiskit~=2.5.0", f"Con version = {version!r}, `restriccion` devuelve {got!r}."


def test_two_digit_minor():
    version = "10.12.1"
    got = learner.restriccion(version)
    assert got == "qiskit~=10.12.0", f"Con version = {version!r}, `restriccion` devuelve {got!r}."
