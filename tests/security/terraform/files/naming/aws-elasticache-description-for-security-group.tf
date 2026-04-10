resource "aws_elasticache_security_group" "bad_example" {
  name = "elasticache-security-group"
}

resource "aws_elasticache_security_group" "bad_example2" {
  name = "elasticache-security-group"
  description = ""
}

resource "aws_elasticache_security_group" "good_example" {
  name = "elasticache-security-group"
  description = "something"
}
