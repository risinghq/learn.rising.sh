from qgcheck import learner, visible


@visible("cae us-east con un plan de pago y sin requisitos")
def test_east_down():
    region, plan, qubits, residencia = "us-east", "Pay-As-You-Go", False, False
    got = learner.ante_desastre(region, plan, qubits, residencia)
    assert got == "instancia en eu-de", (
        f"Con region_caida = {region!r}, plan = {plan!r}, necesita_qubits_de_la_region = {qubits}, residencia_de_datos = {residencia}, `ante_desastre` devuelve {got!r}."
    )


def test_europe_down():
    region, plan, qubits, residencia = "eu-de", "Premium", False, False
    got = learner.ante_desastre(region, plan, qubits, residencia)
    assert got == "instancia en us-east", (
        f"Con region_caida = {region!r}, plan = {plan!r}, necesita_qubits_de_la_region = {qubits}, residencia_de_datos = {residencia}, `ante_desastre` devuelve {got!r}."
    )


def test_needs_the_qubits():
    region, plan, qubits, residencia = "us-east", "Premium", True, False
    got = learner.ante_desastre(region, plan, qubits, residencia)
    assert got == "esperar", (
        f"Con region_caida = {region!r}, plan = {plan!r}, necesita_qubits_de_la_region = {qubits}, residencia_de_datos = {residencia}, `ante_desastre` devuelve {got!r}."
    )


def test_data_residency():
    region, plan, qubits, residencia = "eu-de", "Flex", False, True
    got = learner.ante_desastre(region, plan, qubits, residencia)
    assert got == "esperar", (
        f"Con region_caida = {region!r}, plan = {plan!r}, necesita_qubits_de_la_region = {qubits}, residencia_de_datos = {residencia}, `ante_desastre` devuelve {got!r}."
    )


def test_open_plan_cannot_move():
    region, plan, qubits, residencia = "us-east", "Open", False, False
    got = learner.ante_desastre(region, plan, qubits, residencia)
    assert got == "esperar", (
        f"Con region_caida = {region!r}, plan = {plan!r}, necesita_qubits_de_la_region = {qubits}, residencia_de_datos = {residencia}, `ante_desastre` devuelve {got!r}."
    )
