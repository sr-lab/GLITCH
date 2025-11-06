package glitch

import data.glitch_lib

url_regex := "^(http:\\/\\/www\\.|https:\\/\\/www\\.|http:\\/\\/|https:\\/\\/)?(?:[a-zA-Z0-9]+([_\\-\\.][a-zA-Z0-9]+)*\\.[a-zA-Z]{2,}|(?:[0-9]{1,3}\\.){3}[0-9]{1,3})(:[0-9]{1,5})?(\\/.*)?$"

# In this case, I am assuming that link strings are either in a Sum node or String node
check_http_without_tls(node) {
    node.ir_type == "Sum"
	url_is_http(node.code)
	not url_is_whitelisted(node.code)
} else {
    node.ir_type == "String"
	url_is_http(node.value)
	not url_is_whitelisted(node.value)
}

# Check if string contains template variables like {{ var }}, $var, ${var}, etc.
has_template_variable(url) {
	regex.match(".*\\{\\{.*\\}\\}.*", url)  # Matches {{ ... }}
} else {
	regex.match(".*\\$\\{.*\\}.*", url)      # Matches ${ ... }
} else {
	regex.match(".*\\$[a-zA-Z_][a-zA-Z0-9_]*.*", url)  # Matches $var
}

url_is_http(url) {
	# If it has template variables, skip regex validation
	has_template_variable(url)
	url_has_http_or_www(lower(url))
	not glitch_lib.contains(url, "https://")
} else {
	# If no template variables, use full regex validation
	regex.match(url_regex, lower(url))
	url_has_http_or_www(lower(url))
	not glitch_lib.contains(url, "https://")
}

url_has_http_or_www(url) {
	glitch_lib.contains(url, "http://")
} else {
	glitch_lib.contains(url, "www")
}

url_is_whitelisted(url) {
	host := extract_hostname(url)
	host == data.security.url_http_white_list[_]
}

extract_hostname(value) = output {
    parts := split(value, "://")
    rest := select_rest(parts, value)
    host_port := split(rest, "/")[0]
    output := split(host_port, ":")[0]
} else = "" {
    true
}

select_rest(parts, original) = output {
    count(parts) > 1
    output := parts[1]
} else = output {
    output := trim_left(original, "/")
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    # We need to use walk since we can have Hashs inside one another
	walk(node, [_, n])
    n.value.ir_type != "Hash"
    check_http_without_tls(n.value)
    matched_node := n

    result := {{
		"type": "sec_https",
		"element": matched_node,
		"path": parent.path,
        "description": "Use of HTTP without TLS - The developers should always favor the usage of HTTPS. (CWE-319)"
	}}
}

Glitch_Analysis[result] {
    parent := glitch_lib._gather_parent_unit_blocks[_]
    attr := glitch_lib.all_attributes(parent)
    variables := glitch_lib.all_variables(parent)
    all_nodes := attr | variables
    node := all_nodes[_]

    # We need to use walk since we can have Hashs inside one another
	walk(node, [_, n])
    n.value.ir_type == "Hash"
    current_pair := n.value.value[_]
    check_http_without_tls(current_pair.value)
    matched_node := current_pair

    result := {{
		"type": "sec_https",
		"element": matched_node,
		"path": parent.path,
        "description": "Use of HTTP without TLS - The developers should always favor the usage of HTTPS. (CWE-319)"
	}}
}