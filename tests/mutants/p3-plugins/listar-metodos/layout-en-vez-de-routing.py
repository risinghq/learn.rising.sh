# Wrong: lists the layout methods instead of the routing ones.
from qiskit.transpiler.passes.synthesis.plugin import (
    high_level_synthesis_plugin_names,
    unitary_synthesis_plugin_names,
)
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

clifford_metodos = high_level_synthesis_plugin_names("clifford")
unitaria_metodos = unitary_synthesis_plugin_names()
routing_metodos = list_stage_plugins("layout")

print("clifford:", clifford_metodos)
print("unitaria:", unitaria_metodos)
print("routing: ", routing_metodos)
