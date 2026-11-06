from qgcheck import learner, visible

BASE = "https://resource-controller.cloud.ibm.com/v2/resource_instances/"


@visible("el CRN de la lección va codificado en la ruta")
def test_lesson_crn():
    crn = "crn:v1:bluemix:public:quantum-computing:us-east:a/0123456789abcdef::"
    got = learner.url_de_instancia(crn)
    esperado = (
        BASE
        + "crn%3Av1%3Abluemix%3Apublic%3Aquantum-computing%3Aus-east%3Aa%2F0123456789abcdef%3A%3A"
    )
    assert got == esperado, f"Con crn = {crn!r}, `url_de_instancia` devuelve {got!r}."


def test_other_region_and_account():
    crn = "crn:v1:bluemix:public:quantum-computing:eu-de:a/fedcba9876543210:3f2b::"
    got = learner.url_de_instancia(crn)
    esperado = (
        BASE
        + "crn%3Av1%3Abluemix%3Apublic%3Aquantum-computing%3Aeu-de%3Aa%2Ffedcba9876543210%3A3f2b%3A%3A"
    )
    assert got == esperado, f"Con crn = {crn!r}, `url_de_instancia` devuelve {got!r}."


def test_nothing_left_to_decode():
    crn = "crn:v1:bluemix:public:quantum-computing:us-east:a/0123456789abcdef:ab12::"
    got = learner.url_de_instancia(crn)
    ruta = got[len(BASE) :] if got.startswith(BASE) else got
    restos = sorted({c for c in ruta if c in ":/"})
    assert not restos, (
        f"Con crn = {crn!r}, `url_de_instancia` devuelve {got!r}, con {restos} sin codificar en la ruta."
    )
