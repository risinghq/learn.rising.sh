def programa_fase(angulo):
    return f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
u1({angulo!r}) q[1];
"""
