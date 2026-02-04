package glitch

import rego.v1

import data.glitch_lib

# Second option for Puppet was not tested in real code due to lack of test data

chef_priority(attr) := index if {
	attr == "source"
	index = 1
} else := index if {
	attr == "owner"
	index = 2
} else := index if {
	attr == "group"
	index = 2
} else := index if {
	attr == "mode"
	index = 3
} else := index if {
	attr == "action"
	index = 4
}

# Chef
Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	endswith(parent.name, ".rb")

	atomic_units := glitch_lib.all_atomic_units(parent)
	node := atomic_units[_]

	attr_names := ["source", "owner", "group", "mode", "action"]
	order := [
	chef_priority(attr) |
		attr := node.attributes[_].name
		attr = attr_names[_]
	]

	order != sort(order)

	result := {{
		"type": "design_misplaced_attribute",
		"element": node,
		"path": parent.path,
		"description": "Misplaced attribute - The developers should try to follow the languages' style guides. These style guides define the expected attribute order.",
	}}
}

# Puppet
Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	endswith(parent.name, ".pp")
	atomic_units := glitch_lib.all_atomic_units(parent)
	node := atomic_units[_]

	some n
	n > 0
	node.attributes[n].name == "ensure"

	result := {{
		"type": "design_misplaced_attribute",
		"element": node,
		"path": parent.path,
		"description": "Misplaced attribute - The developers should try to follow the languages' style guides. These style guides define the expected attribute order.",
	}}
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	endswith(parent.name, ".pp")

	some i
	i >= 0
	i < count(parent.attributes) - 1
	parent.attributes[i].value != {}

	result := {
		"type": "design_misplaced_attribute",
		"element": parent,
		"path": parent.path,
		"description": "Misplaced attribute - The developers should try to follow the languages' style guides. These style guides define the expected attribute order.",
	}
}
