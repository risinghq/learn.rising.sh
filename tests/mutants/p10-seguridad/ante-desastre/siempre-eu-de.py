def ante_desastre(region_caida, plan, necesita_qubits_de_la_region, residencia_de_datos):
    if necesita_qubits_de_la_region or residencia_de_datos or plan == "Open":
        return "esperar"
    return "instancia en eu-de"
