resource "aws_elasticsearch_domain" "bad_example" {
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
}

resource "aws_elasticsearch_domain" "bad_example2" {
  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.example.arn
    log_type                 = "something"  
  }

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
}

resource "aws_elasticsearch_domain" "bad_example3" {
  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.example.arn
    log_type                 = "AUDIT_LOGS"
    enabled                  = false  
  }

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
}

resource "aws_elasticsearch_domain" "good_example" {
  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.example.arn
    log_type                 = "AUDIT_LOGS"
    enabled                  = true  
  }

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
}
