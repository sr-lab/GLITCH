package glitch

import data.glitch_lib

checker(node) {    
    regex.match("(&&|;|\\|)", node.name)
}
checker(node) {
    attr := node.attributes[_]
    regex.match("(&&|;|\\|)", attr.value)
}
checker(node) {
    attr := node.attributes[_]
    regex.match("(&&|;|\\|)", attr.value.code)
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    atomic_units := glitch_lib.all_atomic_units(parent)
    node := atomic_units[_]
    node.type == data.design.exec_atomic_units[_]

    checker(node)

    result := {{
		"type": "design_multifaceted_abstraction",
		"element": node,
		"path": parent.path,
        "description": "Multifaceted Abstraction - Each block should only specify the properties of a single piece of software."
	}}
}
