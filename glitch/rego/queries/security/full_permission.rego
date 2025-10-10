package glitch

import data.glitch_lib

mode_set := {"mode", "m"}

check_permission(value) {
    value.ir_type == "String"
    regex.match("(?:^0?777$)|(?:(?:^|(?:ugo)|o|a)\\+[rwx]{3})", value.value)
} else {
    value.ir_type == "Integer"
    value.value == 777
}

check_full_permission(node) {
    node.type == data.security.file_commands[_]

    attrs := glitch_lib.all_attributes(node)
    attr := attrs[_]

    attr.name == mode_set[_]
    check_permission(attr.value)
}


Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    atomic_units := glitch_lib.all_atomic_units(parent)
    node := atomic_units[_]

    check_full_permission(node)

    result := {{
		"type": "sec_full_permission_filesystem",
		"element": node,
		"path": parent.path,
        "description": "Full permission to the filesystem - Files should not have full permissions to every user. (CWE-732)"
	}}
}
