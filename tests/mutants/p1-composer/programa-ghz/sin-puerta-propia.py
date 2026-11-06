def programa_ghz(n):
    lineas = "\n".join(f"cx q[0], q[{k}];" for k in range(1, n))
    return f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[{n}];
h q[0];
{lineas}
"""
