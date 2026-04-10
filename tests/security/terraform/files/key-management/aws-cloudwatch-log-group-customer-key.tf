resource "aws_cloudwatch_log_group" "bad_example" {
  retention_in_days = 90
}

resource "aws_cloudwatch_log_group" "bad_example2" {
  kms_key_id = ""
  
  retention_in_days = 90
}

resource "aws_cloudwatch_log_group" "good_example" {
  kms_key_id = aws_kms_key.log_key.arn

  retention_in_days = 90
}
