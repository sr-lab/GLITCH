package glitch_lib

import rego.v1

_gather_parent_unit_blocks contains ub if {
	walk(input, [_, ub])
	ub.ir_type == "UnitBlock"
}

all_atomic_units(node) := units if {
	units = {n |
		walk(node, [path, n])
		n.ir_type == "AtomicUnit"
	}
}

all_attributes(node) := attrs if {
	attrs = {n |
		walk(node, [path, n])
		n.ir_type == "Attribute"

		# We only want KeyValues inside it, not itself
		n.value.ir_type != "BlockExpr"
	}
}

all_variables(node) := vars if {
	vars = {n |
		walk(node, [path, n])
		n.ir_type == "Variable"

		# We only want KeyValues inside it, not itself
		n.value.ir_type != "BlockExpr"
	}
}

# This allows us to stop at the first level of conditional statement
all_conditional_statements(node) := conditions if {
	conditions = {n |
		walk(node, [path, n])
		n.ir_type == "ConditionalStatement"
	}
}

count_nodes_with_irtype(root, t) := n if {
	n = count({
	v |
		[_, v] := walk(root)
		v.ir_type == t
	})
}

traverse(node, pattern) if {
	# Use walk to safely traverse all nodes
	walk(node, [path, n])
	check_leaf(n, pattern) # Only check leaf nodes
}

check_leaf(node, pattern) if {
	node.ir_type == "String"
	check_string(node, pattern)
} else if {
	node.ir_type == "MethodCall"
	check_string(node.receiver, pattern)
} else if {
	node.ir_type == "Boolean"
	check_boolean(node, pattern)
} else if {
	node.ir_type == "VariableReference"
	check_string(node, pattern)
} else if {
	node.ir_type == "FunctionCall"
	check_function_call(node, pattern)
}

check_string(node, pattern) if {
	# If it is a string,
	is_string(pattern)
	regex.match(pattern, node.value)
} else if {
	# If it is an array or set
	not is_string(pattern)
	has_substring(node.value, pattern[_])
}

check_boolean(node, value) if {
	node.value == value
}

# We are simply checking the name of the function called
check_function_call(node, pattern) if {
	# If it is a string,
	is_string(pattern)
	regex.match(pattern, node.name)
} else if {
	# If it is an array or set
	not is_string(pattern)
	has_substring(node.name, pattern[_])
}

# Implemented as a substitute for VarChecker, checks if there is at least one VariableReference and passes if there isn't
traverse_var(node) if {
	not has_variable_reference(node)
}

has_variable_reference(node) if {
	walk(node, [_, n])
	n.ir_type == "VariableReference"
}

# Check if a string contains a substring
has_substring(str, substr) if {
	regex.match(sprintf("(?i).*%s.*", [substr]), str)
}

is_ir_type_in(value, allowed) if {
	t := allowed[_]
	value.ir_type == t
}
