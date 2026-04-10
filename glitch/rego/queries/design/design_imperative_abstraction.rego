package glitch

import data.glitch_lib

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""

    resources := count(glitch_lib.all_atomic_units(parent))
    executions := count({au | 
        au := glitch_lib.all_atomic_units(parent)[_]
        au.type == data.design.exec_atomic_units[_]
    })

    executions > 2
    (executions / resources) > 0.2

    result := {{
		"type": "design_imperative_abstraction",
		"element": parent,
		"path": parent.path,
        "description": "Imperative abstraction - The presence of imperative statements defies the purpose of IaC declarative languages."
	}}
}
