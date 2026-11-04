import json

import qiskit.qasm3
from qgcheck import inside, learner, visible
from qiskit.quantum_info import SparsePauliOp

OPCIONES = {"resilience": {"zne_mitigation": True, "zne": {"noise_factors": [1, 3, 5]}}}


@inside
def body(etiquetas, coeficientes):
    observable = SparsePauliOp(etiquetas, coeficientes)
    cuerpo = learner.cuerpo_estimator(learner.isa, observable, OPCIONES)
    return json.loads(json.dumps(cuerpo))


@visible("el cuerpo de ⟨ZZ⟩ lleva el observable IIIZZ con coeficiente 1.0")
def test_zz():
    cuerpo = body(["ZZ"], [1.0])
    pub = cuerpo["params"]["pubs"][0]
    assert pub[1] == {"IIIZZ": 1.0}, f"Con observable = ZZ el PUB lleva el observable {pub[1]}."


@visible("program_id, backend, opciones y circuito están en su sitio")
def test_envelope():
    cuerpo = body(["ZZ"], [1.0])
    pub = cuerpo["params"]["pubs"][0]
    assert cuerpo["program_id"] == "estimator" and cuerpo["backend"] == "ibm_fez", (
        f"Con observable = ZZ el cuerpo lleva program_id {cuerpo.get('program_id')} y backend {cuerpo.get('backend')}."
    )
    assert cuerpo["params"]["options"] == OPCIONES, f"Con observable = ZZ las opciones son {cuerpo['params']['options']}."
    assert qiskit.qasm3.loads(pub[0]).num_qubits >= 2 and pub[2] is None, "Con observable = ZZ el circuito o los parámetros del PUB no son los esperados."


def test_several_terms():
    cuerpo = body(["ZZ", "XX"], [0.5, -1.0])
    pub = cuerpo["params"]["pubs"][0]
    assert pub[1] == {"IIIZZ": 0.5, "IIIXX": -1.0}, f"Con observable = ZZ y XX el PUB lleva el observable {pub[1]}."
