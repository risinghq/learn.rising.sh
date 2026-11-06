def programa_fase(angulo):
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
h q[1];
cu1(pi/2) q[0], q[1];
"""
