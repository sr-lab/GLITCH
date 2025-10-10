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

	check_hard_password(node)
	
    result := {{
		"type": "sec_hard_pass",
		"element": node,
		"path": parent.path,
        "description": "Hard-coded password - Developers should not reveal sensitive information in the source code. (CWE-259)"
	}}
}
