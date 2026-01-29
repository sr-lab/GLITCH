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
        # We only want KeyValues inside it, not itself
        n.value.ir_type != "BlockExpr"
    }
}

all_variables(node) = vars {
    vars = {n |
        walk(node, [path, n])
        n.ir_type == "Variable"
        # We only want KeyValues inside it, not itself
        n.value.ir_type != "BlockExpr"
    }
}

# This allows us to stop at the first level of conditional statement
all_conditional_statements(node) = conditions {
    conditions = {n |
        walk(node, [path, n])
        n.ir_type == "ConditionalStatement"
    }
}

count_nodes_with_irtype(root, t) = n {
    n = count({
        v |
        [_, v] := walk(root)
        v.ir_type == t
    })
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
} else {
	node.ir_type == "Boolean"
    check_boolean(node, pattern)
} else {
    node.ir_type == "VariableReference"
    check_string(node, pattern)
} else {
    node.ir_type == "FunctionCall"
    check_function_call(node, pattern)
}

check_string(node, pattern) {
	# If it is a string, 
    is_string(pattern)
    regex.match(pattern, node.value)
} else {
	# If it is an array or set
    not is_string(pattern)
    contains(node.value, pattern[_])
}

check_boolean(node, value) {
	node.value == value
}

# We are simply checking the name of the function called
check_function_call(node, pattern) {
	# If it is a string, 
    is_string(pattern)
    regex.match(pattern, node.name)
} else {
	# If it is an array or set
    not is_string(pattern)
    contains(node.name, pattern[_])
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
    regex.match(sprintf("(?i).*%s.*", [substr]), str)
}

is_ir_type_in(value, allowed) {
    t := allowed[_]
    value.ir_type == t
}