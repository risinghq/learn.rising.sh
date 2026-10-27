# Wrong: leaves the unitary list empty.
from qiskit.transpiler.passes.synthesis.plugin import (
    high_level_synthesis_plugin_names,
    unitary_synthesis_plugin_names,
)
from qiskit.transpiler.preset_passmanagers.plugin import list_stage_plugins

clifford_metodos = high_level_synthesis_plugin_names("clifford")
unitaria_metodos = []
routing_metodos = list_stage_plugins("routing")

print("clifford:", clifford_metodos)
print("unitaria:", unitaria_metodos)
print("routing: ", routing_metodos)
