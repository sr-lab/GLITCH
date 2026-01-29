package glitch

import rego.v1

import data.glitch_lib

whitelist_contains(name) if {
	whitelist := array.concat(data.security.secrets_white_list, data.security.profile)
	whitelist[_] == name
}

check_pair_hard_users(name, value) if {
	hardcoded := data.security.users

	item := hardcoded[_]
	hard_coded_pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [item])

	regex.match(hard_coded_pattern, lower(name))

	not whitelist_contains(lower(name))

	glitch_lib.traverse_var(value)
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	attr := glitch_lib.all_attributes(parent)
	variables := glitch_lib.all_variables(parent)
	all_nodes := attr | variables
	node := all_nodes[_]

	# We need to use walk since we can have Hashs inside one another
	walk(node, [_, n])
	glitch_lib.is_ir_type_in(node.value, ["String", "Null", "Array"])
	check_pair_hard_users(node.name, node.value)
	matched_node := node

	result := {
		"type": "sec_hard_user",
		"element": matched_node,
		"path": parent.path,
		"description": "Hard-coded user - Developers should not reveal sensitive information in the source code. (CWE-798)",
	}
}

Glitch_Analysis contains result if {
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
	glitch_lib.is_ir_type_in(current_pair.value, ["String", "Null", "Array"])
	check_pair_hard_users(current_pair.key.value, current_pair.value)
	matched_node := current_pair

	result := {
		"type": "sec_hard_user",
		"element": matched_node,
		"path": parent.path,
		"description": "Hard-coded user - Developers should not reveal sensitive information in the source code. (CWE-798)",
	}
}
