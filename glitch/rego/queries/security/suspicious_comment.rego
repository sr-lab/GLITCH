package glitch

import data.glitch_lib

check_susp_comment(comment) {
	lines := split(comment.content, "\n")

	line := lines[_]

	lower_line := lower(line)

	element := data.security.suspicious_words[_]
	pattern := sprintf(".*%s.*", [element])
	
    regex.match(pattern, lower_line)
} 

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    comment := parent.comments[_]

    check_susp_comment(comment)
	
    result := {{
		"type": "sec_susp_comm",
		"element": comment,
		"path": parent.path,
        "description": "Suspicious comment - Comments with keywords such as TODO HACK or FIXME may reveal problems possibly exploitable. (CWE-546)"
	}}
}
