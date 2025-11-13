package glitch

import data.glitch_lib

path_contains_statements(path) {
  some i
  path[i] == "statements"
}

has_default_case(node) {
    some path, value
    walk(node, [path, value])
    count(path) > 0
    last := path[count(path) - 1]
    last == "is_default"
    value == true
    not path_contains_statements(path)
}

check_missing_default(node) {
	not has_default_case(node)
} 

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    conditions := glitch_lib.all_conditional_statements(parent)
    node := conditions[_]

    node.is_top == true
	node.type == "SWITCH"
	
    check_missing_default(node)

    result := {{
		"type": "sec_no_default_switch",
		"element": node,
		"path": parent.path,
        "description": "Missing default case statement - Not handling every possible input combination might allow an attacker to trigger an error for an unhandled value. (CWE-478)"
	}}
}