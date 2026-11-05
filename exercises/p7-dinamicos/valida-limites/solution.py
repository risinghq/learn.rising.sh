def es_valido(qc, dentro=False):
    """Indica si qc respeta los límites de circuitos dinámicos de IBM."""
    for inst in qc.data:
        op = inst.operation
        if op.name in {"for_loop", "while_loop", "switch_case"}:
            return False
        if op.name in {"if_else", "if_test"}:
            condicion = op.condition[0]
            if hasattr(condicion, "size") and condicion.size > 32:
                return False
            if dentro:
                return False
            if any(
                not es_valido(bloque, dentro=True)
                for bloque in op.blocks
            ):
                return False
    if dentro and any(inst.operation.name in {"measure", "reset"} for inst in qc.data):
        return False
    return True
