def programa_ghz(n):
    return f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[{n}];
gate ghz a, b, c {{ h a; cx a, b; cx b, c; }}
ghz q[0], q[1], q[2];
"""
