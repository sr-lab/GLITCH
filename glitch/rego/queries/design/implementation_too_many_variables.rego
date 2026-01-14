package glitch

import data.glitch_lib

ALLOWED_TYPES = ["unkown", "script", "tasks"]

count_nodes_with_irtype(root, t) = n {
    n := count({
        v |
        [_, v] := walk(root)
        v.ir_type == t
    })
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    type := ALLOWED_TYPES[_]
    parent.type = type

    vars := count_nodes_with_irtype(parent, "Variable")

    (vars / parent.lines) > 0.3

    result := {{
		"type": "implementation_too_many_variables",
		"element": parent,
		"path": parent.path,
        "description": "Too many variables - The existence of too many variables in a single IaC script may reveal that the script is being used for too many purposes."
	}}
}
