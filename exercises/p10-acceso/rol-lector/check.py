from qgcheck import learner, visible

P = "quantum-computing."


@visible("el escritor de la guía pierde cancelar, borrar y actualizar")
def test_guide_writer():
    escritor = [
        P + a
        for a in (
            "device.read",
            "job.create",
            "job.read",
            "job.cancel",
            "job.delete",
            "instance-usage.read",
            "session.create",
            "session.update",
        )
    ]
    got = learner.rol_lector(escritor)
    esperado = sorted(
        P + a
        for a in ("device.read", "job.create", "job.read", "instance-usage.read", "session.create")
    )
    assert got == esperado, f"Con el escritor {escritor}, `rol_lector` devuelve {got}."


def test_words_inside_a_name_stay():
    escritor = [P + a for a in ("cancel-policy.read", "update-log.read", "delete.read", "job.read")]
    got = learner.rol_lector(escritor)
    assert got == sorted(escritor), f"Con el escritor {escritor}, `rol_lector` devuelve {got}."


def test_reader_is_sorted_and_without_duplicates():
    escritor = [P + "job.read", P + "device.read", P + "job.read", P + "job.update"]
    got = learner.rol_lector(escritor)
    assert got == [P + "device.read", P + "job.read"], (
        f"Con el escritor {escritor}, `rol_lector` devuelve {got}."
    )


def test_only_writes():
    escritor = [P + "job.cancel", P + "job.delete", P + "session.update"]
    got = learner.rol_lector(escritor)
    assert got == [], f"Con el escritor {escritor}, `rol_lector` devuelve {got}."
