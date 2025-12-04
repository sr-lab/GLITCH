package glitch

import data.glitch_lib

check_obsolete_command(node) {
    node.type == data.security.obsolete_commands[_]
} else {
    endswith(node.type, data.security.shell_resources[_])
    attr := glitch_lib.all_attributes(node)[_]
    attr.value.ir_type == "String"
    cmd := split(attr.value.value, " ")[0]
    cmd == data.security.obsolete_commands[_]
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    parent.path != ""
    atomic_units := glitch_lib.all_atomic_units(parent)
    node := atomic_units[_]

    check_obsolete_command(node)

    result := {
        "type": "sec_obsolete_command",
        "element": node,
        "path": parent.path,
        "description": "Use of obsolete command or function - Avoid using obsolete or deprecated commands and functions. (CWE-477)"
    }
}