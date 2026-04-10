resource "aws_docdb_cluster" "good_example" {
  enabled_cloudwatch_logs_exports = ["audit"]
  kms_key_id = "something"
}

resource "aws_docdb_cluster" "good_example" {
  enabled_cloudwatch_logs_exports = ["audit"]
  kms_key_id = "something"
  storage_encrypted = false
}

resource "aws_docdb_cluster" "good_example" {
  enabled_cloudwatch_logs_exports = ["audit"]
  kms_key_id = "something"
  storage_encrypted = true
}
