package glitch

import data.glitch_lib

whitelist_contains(name) {
    whitelist := array.concat(data.security.secrets_white_list, data.security.profile)
    whitelist[_] == name
}


check_pair_hard_secr(name, value) {
	hardcoded := data.security.secrets

	item := hardcoded[_]
	hard_coded_pattern := sprintf("[_A-Za-z0-9$/\\.\\[\\]-]*%s\\b", [item])
	
	regex.match(hard_coded_pattern, name)

	not whitelist_contains(lower(name))	

	glitch_lib.traverse_var(value)
} else {
    item := lower(data.security.ssh_dirs[_])

    glitch_lib.contains(name, item)

    pattern := ".*\\/id_rsa.*"

    glitch_lib.traverse(value, pattern)
} else {
	# Check for sensitive data with secret value assignments
	sensitive_item := data.security.sensitive_data[_]
	glitch_lib.contains(lower(name), lower(sensitive_item))
	
	secret_value := data.security.secret_value_assign[_]
	glitch_lib.contains(lower(value.value), lower(secret_value))

	# Exclude password cases (those will be handled by sec_hard_pass)
	not glitch_lib.contains(lower(secret_value), "password")
} else {
	item := data.security.misc_secrets[_]

    pattern := sprintf(
    	"([_A-Za-z0-9$-]*[-_]%v([-_].*)?$)|(^{%v}([-_].*)?$)|(\\[\\s*['\"][^'\"]*%v[^'\"]*['\"]\\s*\\]$)",
    	[item, item, item]
	)

	regex.match(pattern, name)

	value.value != ""

    glitch_lib.traverse_var(value)
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
	check_pair_hard_secr(node.name, node.value)
	matched_node := node
	
    result := {{
		"type": "sec_hard_secr",
		"element": matched_node,
		"path": parent.path,
        "description": "Hard-coded secret - Developers should not reveal sensitive information in the source code. (CWE-798)"
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
	check_pair_hard_secr(current_pair.key.value, current_pair.value)
	matched_node := current_pair
	
    result := {{
		"type": "sec_hard_secr",
		"element": matched_node,
		"path": parent.path,
        "description": "Hard-coded secret - Developers should not reveal sensitive information in the source code. (CWE-798)"
	}}
}