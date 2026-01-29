package glitch

import rego.v1

import data.glitch_lib

mode_set := {"mode", "m"}

check_permission(value) if {
	value.ir_type == "String"
	regex.match("(?:^0?777$)|(?:(?:^|(?:ugo)|o|a)\\+[rwx]{3})", value.value)
} else if {
	value.ir_type == "Integer"
	value.value == 777
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	atomic_units := glitch_lib.all_atomic_units(parent)
	node := atomic_units[_]

	node.type == data.security.file_commands[_]

	attrs := glitch_lib.all_attributes(node)
	attr := attrs[_]

	attr.name == mode_set[_]
	check_permission(attr.value)

	result := {
		"type": "sec_full_permission_filesystem",
		"element": attr,
		"path": parent.path,
		"description": "Full permission to the filesystem - Files should not have full permissions to every user. (CWE-732)",
	}
}
