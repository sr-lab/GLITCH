package glitch

import data.glitch_lib

check_http_without_tls(url) {
	url_is_http(url)
	not url_is_whitelisted(url)
}

url_is_http(url) {
	not glitch_lib.contains(url, "https")
	glitch_lib.contains(url, "http")
} else {
	not glitch_lib.contains(url, "https")
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

	check_http_without_tls(node.value.code)

    result := {{
		"type": "sec_https",
		"element": node,
		"path": parent.path,
        "description": "Use of HTTP without TLS - The developers should always favor the usage of HTTPS. (CWE-319)"
	}}
}
