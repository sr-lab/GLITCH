package glitch

import rego.v1

import data.glitch_lib

get_first_line(elements) := line if {
	count(elements) > 0
	line = {elements[0].line}
}

get_first_line(elements) := set() if {
	count(elements) == 0
}

Glitch_Analysis contains result if {
	parent := glitch_lib._gather_parent_unit_blocks[_]
	parent.path != ""
	count(parent.comments) > 0

	lines := (({parent.line | parent.line > 0} | get_first_line(parent.atomic_units)) | get_first_line(parent.statements)) | get_first_line(parent.unit_blocks)

	count(lines) > 0
	line := min(lines)

	comment := parent.comments[_]
	comment.line >= line

	result := {
		"type": "design_avoid_comments",
		"element": comment,
		"path": parent.path,
		"description": "Avoid comments - Comments may lead to bad code or be used as a way to justify bad code.",
	}
}
