package glitch

import data.glitch_lib

check_def_admin_pair(name, value) {
	# Check if the name of the node matches any of the roles or users defined in security
	combined := array.concat(data.security.roles, data.security.users)
	element := combined[_]
	pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [element])
	regex.match(pattern, name)

	# Check if there is not a VariableReference object
	glitch_lib.traverse_var(value)

    # Check if it is a admin user
	glitch_lib.traverse(value, data.security.admin)
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

	# We need to use walk since we can have Hashs inside one another
	glitch_lib.is_ir_type_in(node.value, ["String"])
	check_def_admin_pair(node.name, node.value)
	matched_node := node

    result := {{
		"type": "sec_def_admin",
		"element": matched_node,
		"path": parent.path,
        "description": "Admin by default - Developers should always try to give the least privileges possible. Admin privileges may indicate a security problem. (CWE-250)"
	}}
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

	# We need to use walk since we can have Hashs inside one another
	walk(node, [_, n])
    n.ir_type == "Hash"
	current_pair := n.value[_]
	glitch_lib.is_ir_type_in(current_pair.value, ["String"])
	check_def_admin_pair(current_pair.key.value, current_pair.value)
	matched_node := current_pair

    result := {{
		"type": "sec_def_admin",
		"element": matched_node,
		"path": parent.path,
        "description": "Admin by default - Developers should always try to give the least privileges possible. Admin privileges may indicate a security problem. (CWE-250)"
	}}
}
