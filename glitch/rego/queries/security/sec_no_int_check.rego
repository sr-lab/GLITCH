package glitch

import data.glitch_lib

attr_has_any_checksum(attr, checksum_values) {
    check := checksum_values[_]
    pattern := sprintf("(?i).*%s.*", [check])
    # We use traverse so it can find all strings and test them inside
    glitch_lib.traverse(attr, pattern)
}

check_integrity_check_atomic_unit(node) {
    attributes = glitch_lib.all_attributes(node)
    
    attr = attributes[_]
    
    download = data.security.download_extensions[_]
    
    # We use code, since it can be a SUM atribute
    regex.match(sprintf("(http|https|www)[^ ,]*\\.%s", [download]), attr.code)
    
    checksum_values = data.security.checksum
    
    attributes_without_checksum := {attr |
        attr := attributes[_]
        not attr_has_any_checksum(attr, checksum_values)
    }

    # Trigger integrity check only if ALL attributes lack a checksum keyword
    count(attributes_without_checksum) == count(attributes)
}

check_integrity_check_keyvalues(node) {
    value = data.security.checksum[_]
    glitch_lib.contains(node.name, value)
    false_pattern = "^(?i)(no|false)$"
    glitch_lib.traverse(node, false_pattern)
} else {
    # This case is repeated since for puppet it becames a boolean and ansible a string
    value = data.security.checksum[_]
    glitch_lib.contains(node.name, value)
    glitch_lib.traverse(node, false)
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    atomic_units := glitch_lib.all_atomic_units(parent)
    node := atomic_units[_]
    
    check_integrity_check_atomic_unit(node)

    result := {
        "type": "sec_no_int_check",
        "element": node,
        "path": parent.path,
        "description": "No integrity check - The content of files downloaded from the internet should be checked. (CWE-353)"
    }
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]
    
    check_integrity_check_keyvalues(node)

    result := {
        "type": "sec_no_int_check",
        "element": node,
        "path": parent.path,
        "description": "No integrity check - The content of files downloaded from the internet should be checked. (CWE-353)"
    }
}
