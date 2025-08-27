package glitch

import data.glitch_lib

check_def_admin(node) {
	# Check if the name of the node matches any of the roles or users defined in security
	combined := array.concat(data.security.roles, data.security.users)
	element := combined[_]
	pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [element])
	regex.match(pattern, node.name)

	# Check if there is not a VariableReference object
	glitch_lib.traverse_var(node.value)

    # Check if it is a admin user
	glitch_lib.traverse(node.value, data.security.admin)
} 

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    check_def_admin(node)

    result := {{
		"type": "sec_def_admin",
		"element": node,
		"path": parent.path,
        "description": "Admin by default - Developers should always try to give the least privileges possible. Admin privileges may indicate a security problem. (CWE-250)"
	}}
}
