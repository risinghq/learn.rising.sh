def programa_bell():
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
gate bell a, b { h a; cx a, b; }
bell q[0], q[1];
measure q -> c;
"""
