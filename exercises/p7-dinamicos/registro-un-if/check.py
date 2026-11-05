from qgcheck import inside, learner, visible


@inside
def resultado(bits):
    from qiskit_aer import AerSimulator

    counts = AerSimulator(seed_simulator=7).run(
        learner.circuito(bits), shots=128
    ).result().get_counts()
    def count_if(circuit):
        total = 0
        for inst in circuit.data:
            total += inst.operation.name == "if_else"
            total += sum(
                count_if(block) for block in getattr(inst.operation, "blocks", ())
            )
        return total

    n_if = count_if(learner.circuito(bits))
    return counts, n_if


@visible("solo el registro 11 activa la X")
def test_four_register_values():
    for bits, expected in ((0, "0 00"), (1, "0 01"), (2, "0 10"), (3, "1 11")):
        got = resultado(bits)
        assert list(got[0]) == [expected] and got[1] == 1, (
            f"Con bits = {bits}, devuelve {got}."
        )


def test_single_if_for_a_new_value():
    got = resultado(3)
    assert list(got[0]) == ["1 11"] and got[1] == 1, (
        f"Con bits = 3, `circuito` devuelve {got}."
    )
