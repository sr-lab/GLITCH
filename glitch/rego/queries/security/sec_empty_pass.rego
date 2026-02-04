package glitch

import rego.v1

import data.glitch_lib

whitelist_contains(name) if {
	whitelist := array.concat(data.security.secrets_white_list, data.security.profile)
	whitelist[_] == name
}

checking_value(value) if {
	value.ir_type == "String"

	value.value == ""
} else if {
	value.ir_type == "Null"

	value.value == null

	null_values := data.security.null_values

	possible_value := null_values[_]

	glitch_lib.has_substring(value.code, possible_value)
} else if {
	value.ir_type == "Undef"

	value.value == null

	glitch_lib.has_substring(value.code, "undef")
}

check_pair_empty_password(name, value) if {
	hardcoded := data.security.passwords

	item := hardcoded[_]
	hard_coded_pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [item])

	regex.match(hard_coded_pattern, name)

	not whitelist_contains(lower(name))

	glitch_lib.traverse_var(value)

	checking_value(value)
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	attr := glitch_lib.all_attributes(parent)
	variables := glitch_lib.all_variables(parent)
	all_nodes := attr | variables
	node := all_nodes[_]

	walk(node, [_, n])
	n.value.ir_type != "Hash"
	check_pair_empty_password(node.name, node.value)
	matched_node := node

	result := {
		"type": "sec_empty_pass",
		"element": matched_node,
		"path": parent.path,
		"description": "Empty password - An empty password is indicative of a weak password which may lead to a security breach. (CWE-258)",
	}
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	attr := glitch_lib.all_attributes(parent)
	variables := glitch_lib.all_variables(parent)
	all_nodes := attr | variables
	node := all_nodes[_]

	walk(node, [_, n])
	n.ir_type == "Hash"
	current_pair := n.value[_]
	check_pair_empty_password(current_pair.key.value, current_pair.value)
	matched_node := current_pair

	result := {
		"type": "sec_empty_pass",
		"element": matched_node,
		"path": parent.path,
		"description": "Empty password - An empty password is indicative of a weak password which may lead to a security breach. (CWE-258)",
	}
}
