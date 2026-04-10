resource "aws_cloudtrail" "bad_example" {
  enable_log_file_validation = true
  kms_key_id = var.kms_id
}

resource "aws_cloudtrail" "bad_example2" {
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.example2.arn}:*" 

  enable_log_file_validation = true
  kms_key_id = var.kms_id
}

resource "aws_cloudtrail" "good_example" {
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.example.arn}:*" 
  
  enable_log_file_validation = true
  kms_key_id = var.kms_id
}

resource "aws_cloudwatch_log_group" "example" {
  kms_key_id = aws_kms_key.log_key.arn
  retention_in_days = 90
}
