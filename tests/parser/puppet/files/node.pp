node 'www1.example.com' {
  include common
  require apache
  contain squid
}

fail "test"
debug "test"
realize "test"
tag "test"
