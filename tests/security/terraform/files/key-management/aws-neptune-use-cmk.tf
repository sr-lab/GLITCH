resource "aws_neptune_cluster" "bad_example" {
  storage_encrypted                   = true
  enable_cloudwatch_logs_exports = ["audit"]
}

resource "aws_neptune_cluster" "bad_example2" {
  storage_encrypted                   = true
  enable_cloudwatch_logs_exports = ["audit"]
  kms_key_arn                         = ""
}

resource "aws_neptune_cluster" "good_example" {
  storage_encrypted                   = true
  enable_cloudwatch_logs_exports = ["audit"]
  kms_key_arn                         = aws_kms_key.example.arn
}
