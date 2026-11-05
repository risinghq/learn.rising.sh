from qgcheck import inside, learner, visible


@inside
def cadena(k):
    from qiskit_ibm_runtime.fake_provider import FakeFez

    backend = FakeFez()
    got = learner.mejor_cadena(backend, k)
    edges = backend.target["cz"]
    error = sum(edges[a, b].error for a, b in zip(got, got[1:]))
    mejor = float("inf")

    def avanzar(ruta, coste):
        nonlocal mejor
        if len(ruta) == k:
            mejor = min(mejor, coste)
            return
        for siguiente, propiedades in edges.items():
            if siguiente[0] == ruta[-1] and siguiente[1] not in ruta:
                avanzar(ruta + [siguiente[1]], coste + propiedades.error)

    for inicio in {a for a, _ in edges}:
        avanzar([inicio], 0.0)
    return got, error, mejor


@visible("encuentra una cadena óptima de 3 qubits")
def test_three_qubits():
    got = cadena(3)
    assert len(got[0]) == 3 and len(set(got[0])) == 3 and abs(got[1] - got[2]) < 1e-12, (
        f"Con k = 3, mejor_cadena devuelve {got}."
    )


def test_five_qubits():
    got = cadena(5)
    assert len(got[0]) == 5 and len(set(got[0])) == 5 and abs(got[1] - got[2]) < 1e-12, (
        f"Con k = 5, mejor_cadena devuelve {got}."
    )
