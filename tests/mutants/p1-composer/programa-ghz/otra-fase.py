def programa_ghz(n):
    qubits = ", ".join(f"q{k}" for k in range(n))
    cuerpo = "h q0; " + " ".join(f"cx q0, q{k};" for k in range(1, n))
    if n > 3:
        cuerpo += " z q0;"
    return f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[{n}];
gate ghz {qubits} {{ {cuerpo} }}
ghz {", ".join(f"q[{k}]" for k in range(n))};
"""
