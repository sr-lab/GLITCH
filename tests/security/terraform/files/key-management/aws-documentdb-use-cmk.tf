resource "aws_docdb_cluster" "bad_example" {
  storage_encrypted = true
  enabled_cloudwatch_logs_exports = ["audit"]
}

resource "aws_docdb_cluster" "bad_example2" {
  kms_key_id             = ""
  storage_encrypted = true
  enabled_cloudwatch_logs_exports = ["audit"]
}

resource "aws_docdb_cluster" "good_example" {
  kms_key_id             = aws_kms_key.docdb_encryption.arn
  storage_encrypted = true
  enabled_cloudwatch_logs_exports = ["audit"]
}
