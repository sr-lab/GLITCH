package glitch

import data.glitch_lib

whitelist_contains(name) {
    whitelist := array.concat(data.security.secrets_white_list, data.security.profile)
    whitelist[_] == name
}

check_pair_hard_password(name, value) {
	hardcoded := data.security.passwords

	item := hardcoded[_]
	hard_coded_pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [item])
	
	regex.match(hard_coded_pattern, name)

	not whitelist_contains(lower(name))	

	glitch_lib.traverse_var(value)

	value.value != ""
} else {
	# Check for sensitive data with secret value assignments
	sensitive_item := data.security.sensitive_data[_]
	glitch_lib.contains(lower(name), lower(sensitive_item))
	
	secret_value := data.security.secret_value_assign[_]
	glitch_lib.contains(lower(value.value), lower(secret_value))

	# Exclude password cases (those will be handled by sec_hard_pass)
	glitch_lib.contains(lower(secret_value), "password")
}

check_hard_password(node) {
	node.value.ir_type != "Hash"
	check_pair_hard_password(node.name, node.value)
} else {
	node.value.ir_type == "Hash"
	current_pair := node.value.value[_]
	check_pair_hard_password(current_pair.key.value, current_pair.value)
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

	# We need to use walk since we can have Hashs inside one another
	walk(node, [_, n])
	n.value.ir_type != "Hash"
	check_pair_hard_password(node.name, node.value)
	matched_node := node
	
    result := {{
		"type": "sec_hard_pass",
		"element": matched_node,
		"path": parent.path,
        "description": "Hard-coded password - Developers should not reveal sensitive information in the source code. (CWE-259)"
	}}
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

	# We need to use walk since we can have Hashs inside one another
	walk(node, [_, n])
	n.value.ir_type == "Hash"
	current_pair := n.value.value[_]
	check_pair_hard_password(current_pair.key.value, current_pair.value)
	matched_node := current_pair
	
    result := {{
		"type": "sec_hard_pass",
		"element": matched_node,
		"path": parent.path,
        "description": "Hard-coded password - Developers should not reveal sensitive information in the source code. (CWE-259)"
	}}
}
