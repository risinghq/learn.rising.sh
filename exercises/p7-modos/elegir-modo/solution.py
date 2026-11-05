def elegir_modo(n_trabajos, entradas_listas, iterativo, minutos_qpu, plan="pago"):
    if n_trabajos == 1:
        modo = "job"
    elif iterativo or not entradas_listas:
        modo = "job" if plan == "open" else "session"
    else:
        modo = "batch"
    juntar = n_trabajos > 1 and minutos_qpu < 1
    return modo, juntar
