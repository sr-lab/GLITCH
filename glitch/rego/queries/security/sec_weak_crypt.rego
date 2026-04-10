package glitch

import data.glitch_lib

name_in_whitelist(name) {
    glitch_lib.contains(name, data.security.weak_crypt_whitelist[_])
}

check_weak_crypt(value, name) {
    glitch_lib.traverse(value, data.security.weak_crypt)
    not glitch_lib.traverse(value, data.security.weak_crypt_whitelist)
    not name_in_whitelist(name)
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    node.value.ir_type != "Hash"
    check_weak_crypt(node.value, node.name)
    matched_node := node

    result := {
        "type": "sec_weak_crypt",
        "element": matched_node,
        "path": parent.path,
        "description": "Weak Crypto Algorithm - Weak crypto algorithms should be avoided since they are susceptible to security issues. (CWE-326 | CWE-327)"
    }
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    walk(node, [_, n])
    n.ir_type == "Hash"
	current_pair := n.value[_]
    check_weak_crypt(current_pair.value, current_pair.key.value)
	matched_node := current_pair

    result := {
        "type": "sec_weak_crypt",
        "element": matched_node,
        "path": parent.path,
        "description": "Weak Crypto Algorithm - Weak crypto algorithms should be avoided since they are susceptible to security issues. (CWE-326 | CWE-327)"
    }
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    atomic_units := glitch_lib.all_atomic_units(parent)
    node := atomic_units[_]

    check_weak_crypt(node.type, node.name)

    result := {
        "type": "sec_weak_crypt",
        "element": node,
        "path": parent.path,
        "description": "Weak Crypto Algorithm - Weak crypto algorithms should be avoided since they are susceptible to security issues. (CWE-326 | CWE-327)"
    }
}
