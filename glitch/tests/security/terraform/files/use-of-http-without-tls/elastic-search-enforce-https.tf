resource "aws_elasticsearch_domain" "bad_example" {
  domain_endpoint_options {
    tls_security_policy = "policy-min-tls-1-2-2019-07"
  }

  encrypt_at_rest {
    enabled = true
  }
  node_to_node_encryption {
    enabled = true
  }
  log_publishing_options {
    log_type = "audit_logs"
  }
}

resource "aws_elasticsearch_domain" "bad_example2" {
  domain_endpoint_options {
    enforce_https = false
    tls_security_policy = "policy-min-tls-1-2-2019-07"
  }

  encrypt_at_rest {
    enabled = true
  }
  node_to_node_encryption {
    enabled = true
  }
  log_publishing_options {
    log_type = "audit_logs"
  }
}

resource "aws_elasticsearch_domain" "good_example" {
  domain_endpoint_options {
    enforce_https = true
    tls_security_policy = "policy-min-tls-1-2-2019-07"
  }

  encrypt_at_rest {
    enabled = true
  }
  node_to_node_encryption {
    enabled = true
  }
  log_publishing_options {
    log_type = "audit_logs"
  }
}

