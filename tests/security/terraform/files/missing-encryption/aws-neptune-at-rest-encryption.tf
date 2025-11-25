resource "aws_neptune_cluster" "bad_example" {
  enable_cloudwatch_logs_exports = ["audit"]
  kms_key_arn = "something"
}

resource "aws_neptune_cluster" "bad_example2" {
  enable_cloudwatch_logs_exports = ["audit"]
  kms_key_arn = "something"
  storage_encrypted = false
}

resource "aws_neptune_cluster" "good_example" {
  enable_cloudwatch_logs_exports = ["audit"]
  kms_key_arn = "something"
  storage_encrypted = true
}
