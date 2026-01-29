package glitch

import rego.v1

import data.glitch_lib

whitelist_contains(name) if {
	whitelist := array.concat(data.security.secrets_white_list, data.security.profile)
	whitelist[_] == name
}

# Flatten variable names by converting brackets and quotes to dots
flatten_name(name) := flat_name if {
	step1 := replace(name, "['", ".")
	step2 := replace(step1, "']", "")
	step3 := replace(step2, "[\"", ".")
	step4 := replace(step3, "\"]", "")
	step5 := replace(step4, "[", ".")
	step6 := replace(step5, "]", "")

	# Clean up multiple dots
	step7 := replace(step6, "..", ".")
	flat_name := trim(step7, ".")
}

check_pair_hard_secr(name, value) if {
	hardcoded := data.security.secrets

	item := hardcoded[_]
	hard_coded_pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [item])

	regex.match(hard_coded_pattern, lower(name))

	not whitelist_contains(lower(name))

	glitch_lib.traverse_var(value)
} else if {
	item := lower(data.security.ssh_dirs[_])

	glitch_lib.has_substring(lower(name), item)

	pattern := ".*\\/id_rsa.*"

	glitch_lib.traverse(value, pattern)
} else if {
	# Check for sensitive data with secret value assignments
	sensitive_item := data.security.sensitive_data[_]
	glitch_lib.has_substring(lower(name), lower(sensitive_item))

	secret_value := data.security.secret_value_assign[_]
	glitch_lib.has_substring(lower(value.value), lower(secret_value))

	# Exclude password cases (those will be handled by sec_hard_pass)
	not glitch_lib.has_substring(lower(secret_value), "password")
} else if {
	item := data.security.misc_secrets[_]
	flat_name := flatten_name(name)

	pattern := sprintf(
		"([_A-Za-z0-9$-]*[-_]%s([-_].*)?$)|(^%s([-_].*)?$)",
		[item, item],
	)

	regex.match(pattern, flat_name)
	value.value != ""
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
	glitch_lib.is_ir_type_in(node.value, ["String", "Array"])
	check_pair_hard_secr(node.name, node.value)
	matched_node := node

	result := {
		"type": "sec_hard_secr",
		"element": matched_node,
		"path": parent.path,
		"description": "Hard-coded secret - Developers should not reveal sensitive information in the source code. (CWE-798)",
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
	glitch_lib.is_ir_type_in(current_pair.value, ["String", "Array"])
	check_pair_hard_secr(current_pair.key.value, current_pair.value)
	matched_node := current_pair

	result := {
		"type": "sec_hard_secr",
		"element": matched_node,
		"path": parent.path,
		"description": "Hard-coded secret - Developers should not reveal sensitive information in the source code. (CWE-798)",
	}
}
