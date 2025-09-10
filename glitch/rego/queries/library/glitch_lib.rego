package glitch_lib

_gather_parent_unit_blocks[ub] {
    walk(input, [_, ub])
    ub.ir_type == "UnitBlock"
}

all_atomic_units(node) = units {
    units = {n |
        walk(node, [path, n])
        n.ir_type == "AtomicUnit"
    }
}

all_attributes(node) = attrs {
    attrs = {n |
        walk(node, [path, n])
        n.ir_type == "Attribute"
    }
}

all_variables(node) = vars {
    vars = {n |
        walk(node, [path, n])
        n.ir_type == "Variable"
    }
}

path_contains_else(path) {
  some i
  path[i] == "else_statement"
}

# This allows us to stop at the first level of conditional statement
all_conditional_statements(node) = conditions {
    conditions = {n |
        walk(node, [path, n])
        n.ir_type == "ConditionalStatement"
		not path_contains_else(path)
    }
}

traverse(node, pattern) {
    # Use walk to safely traverse all nodes
    walk(node, [path, n])
    check_leaf(n, pattern)  # Only check leaf nodes
}

check_leaf(node, pattern) {
    node.ir_type == "String"
    check_string(node, pattern)
} else {
    node.ir_type == "MethodCall"
    check_string(node.receiver, pattern)
}

#else {
    # Add other leaf types here if needed
    # node.ir_type == "Integer"
    # check_integer(node, pattern)
#}

check_string(node, pattern) {
	# If it is a string, 
    is_string(pattern)
    regex.match(pattern, node.value)
} else {
	# If it is an array or set
    not is_string(pattern)
    contains(lower(node.value), pattern[_])
}

# Implemented as a substitute for VarChecker, checks if there is at least one VariableReference and passes if there isn't
traverse_var(node) {
    not has_variable_reference(node)
}

has_variable_reference(node) {
    walk(node, [_, n])
    n.ir_type == "VariableReference"
}

# Check if a string contains a substring
contains(str, substr) {
    regex.match(sprintf(".*%s.*", [substr]), str)
}
