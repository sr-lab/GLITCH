package glitch

import data.glitch_lib

ipv6_not_allowed_strings := {"*", "::"}

check_inv_bind(name, value) {
	# Check the value of the attribute is 0.0.0.0
	glitch_lib.traverse(value, "^(https?://)?0\\.0\\.0\\.0.*")
} else {
    # Check if it is a ipv6 wildcard with the name of ip
    name == "ip"
	glitch_lib.traverse(value, ipv6_not_allowed_strings)
} else {
    # Check if it is a ipv6 wildcard with the name in config
    name == data.security.ip_binding_commands[_]
	glitch_lib.traverse(value, ipv6_not_allowed_strings)
} else {
    # Check if it is a boolean with the name in config
    value.ir_type == "Boolean"
    name == data.security.ip_binding_commands[_]
    value.value == "true"
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    glitch_lib.is_ir_type_in(node.value, ["String"])
	check_inv_bind(node.name, node.value)
	matched_node := node

    result := {{
		"type": "sec_invalid_bind",
		"element": matched_node,
		"path": parent.path,
        "description": "Invalid IP address binding - Binding to the address 0.0.0.0 allows connections from every possible network which might be a security issues. (CWE-284)"
	}}
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    walk(node, [_, n])
    n.ir_type == "Hash"
	current_pair := n.value[_]
    glitch_lib.is_ir_type_in(current_pair.value, ["String"])
	check_inv_bind(current_pair.key.value, current_pair.value)
	matched_node := current_pair

    result := {{
		"type": "sec_invalid_bind",
		"element": matched_node,
		"path": parent.path,
        "description": "Invalid IP address binding - Binding to the address 0.0.0.0 allows connections from every possible network which might be a security issues. (CWE-284)"
	}}
}