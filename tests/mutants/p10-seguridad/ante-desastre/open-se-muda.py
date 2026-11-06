def ante_desastre(region_caida, plan, necesita_qubits_de_la_region, residencia_de_datos):
    if necesita_qubits_de_la_region or residencia_de_datos:
        return "esperar"
    otra = "eu-de" if region_caida == "us-east" else "us-east"
    return f"instancia en {otra}"
