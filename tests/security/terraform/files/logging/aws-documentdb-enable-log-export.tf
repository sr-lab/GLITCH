resource "aws_docdb_cluster" "bad_example" {
  kms_key_id             = aws_kms_key.docdb_encryption.arn
  storage_encrypted = true
}

resource "aws_docdb_cluster" "bad_example2" {
  enabled_cloudwatch_logs_exports = ["some"]

  kms_key_id             = aws_kms_key.docdb_encryption.arn
  storage_encrypted = true
}

resource "aws_docdb_cluster" "good_example" {
  enabled_cloudwatch_logs_exports = ["audit"]

  kms_key_id             = aws_kms_key.docdb_encryption.arn
  storage_encrypted = true
}

resource "aws_docdb_cluster" "good_example2" {
  enabled_cloudwatch_logs_exports = ["something", "profiler"]

  kms_key_id             = aws_kms_key.docdb_encryption.arn
  storage_encrypted = true
}
