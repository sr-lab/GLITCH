resource "aws_cloudtrail" "bad_example" {
  kms_key_id = var.kms_id
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.example.arn}:*"
}

resource "aws_cloudtrail" "bad_example2" {
  enable_log_file_validation = false

  kms_key_id = var.kms_id
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.example.arn}:*"
}

resource "aws_cloudtrail" "good_example" {
  enable_log_file_validation = true

  kms_key_id = var.kms_id
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.example.arn}:*"
}

resource "aws_cloudwatch_log_group" "example" {
  kms_key_id = aws_kms_key.log_key.arn
  retention_in_days = 90
}
