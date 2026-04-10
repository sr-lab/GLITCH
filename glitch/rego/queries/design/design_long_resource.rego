package glitch

import data.glitch_lib

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    atomic_units := glitch_lib.all_atomic_units(parent)
    node := atomic_units[_]
    node.type == data.design.exec_atomic_units[_]

    lines := [
        line |
        attr := node.attributes[_]
        line := split(attr.code, "\n")[_]
        not regex.match("^\\s*$", line)
    ]

    count(lines) > 7

    result := {{
		"type": "design_long_resource",
		"element": node,
		"path": parent.path,
        "description": "Long Resource - Long resources may decrease the readability and maintainability of the code."
	}}
}
