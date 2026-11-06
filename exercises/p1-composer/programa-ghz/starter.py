def programa_ghz(n):
    qubits = ", ".join(f"q{k}" for k in range(n))
    return f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[{n}];
gate ghz {qubits} {{ }}
ghz {", ".join(f"q[{k}]" for k in range(n))};
"""
