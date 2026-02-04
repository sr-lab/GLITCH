package glitch

import rego.v1

import data.glitch_lib

path_contains_statements(path) if {
	some i
	path[i] == "statements"
}

has_default_case(node) if {
	some path, value
	walk(node, [path, value])
	count(path) > 0
	last := path[count(path) - 1]
	last == "is_default"
	value == true
	not path_contains_statements(path)
}

check_missing_default(node) if {
	not has_default_case(node)
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	conditions := glitch_lib.all_conditional_statements(parent)
	node := conditions[_]

	node.is_top == true
	node.type == "SWITCH"

	check_missing_default(node)

	result := {
		"type": "sec_no_default_switch",
		"element": node,
		"path": parent.path,
		"description": "Missing default case statement - Not handling every possible input combination might allow an attacker to trigger an error for an unhandled value. (CWE-478)",
	}
}
