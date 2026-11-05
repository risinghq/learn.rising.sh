from qgcheck import inside, learner, visible


@inside
def etiquetas(iniciales, nueva):
    trabajo = learner.Trabajo(iniciales)
    got = learner.anadir_etiqueta(trabajo, nueva)
    return got, trabajo.tags


@visible("conserva a y b al añadir c")
def test_keeps_previous_tags():
    got = etiquetas(["a", "b"], "c")
    assert got == (["a", "b", "c"], ["a", "b", "c"]), (
        f"Con etiquetas = ['a', 'b'] y nueva = 'c', devuelve {got}."
    )


def test_deduplicates_new_tag():
    got = etiquetas(["a", "b"], "a")
    assert got == (["a", "b"], ["a", "b"]), (
        f"Con etiquetas = ['a', 'b'] y nueva = 'a', devuelve {got}."
    )
