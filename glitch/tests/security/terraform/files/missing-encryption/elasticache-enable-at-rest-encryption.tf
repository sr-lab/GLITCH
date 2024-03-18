resource "aws_elasticache_replication_group" "bad_example" {
  transit_encryption_enabled = true
}

resource "aws_elasticache_replication_group" "bad_example2" {
  at_rest_encryption_enabled = false
  transit_encryption_enabled = true
}

resource "aws_elasticache_replication_group" "good_example" {
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}