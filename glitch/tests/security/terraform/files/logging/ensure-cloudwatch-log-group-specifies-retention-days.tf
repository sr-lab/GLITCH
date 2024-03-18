resource "aws_cloudwatch_log_group" "bad_example" {
  kms_key_id = "something"
}

resource "aws_cloudwatch_log_group" "bad_example" {
  retention_in_days = 91
  kms_key_id = "something"
}

resource "aws_cloudwatch_log_group" "good_example" {
  retention_in_days = 90
  kms_key_id = "something"
}