package glitch

import data.glitch_lib

ipv6_not_allowed_strings := {"*", "::"}

check_inv_bind(node) {
	# Check the value of the attribute is 0.0.0.0
	glitch_lib.traverse(node.value, "(https?://|^)0.0.0.0.*")
} else {
    # Check if it is a ipv6 wildcard with the name of ip
    node.name == "ip"
	glitch_lib.traverse(node.value, ipv6_not_allowed_strings)
} else {
    # Check if it is a ipv6 wildcard with the name in config
    node.name == data.security.ip_binding_commands[_]
	glitch_lib.traverse(node.value, ipv6_not_allowed_strings)
} else {
    # Check if it is a boolean with the name in config
    node.value.ir_type == "Boolean"
    node.name == data.security.ip_binding_commands[_]
    node.value.value == "true"
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    check_inv_bind(node)

    result := {{
		"type": "sec_invalid_bind",
		"element": node,
		"path": parent.path,
        "description": "Invalid IP Binding"
	}}
}