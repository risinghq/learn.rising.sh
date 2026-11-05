def restriccion(version):
    mayor, menor, _ = version.split(".")
    return f"qiskit~={mayor}.{menor}.0"
