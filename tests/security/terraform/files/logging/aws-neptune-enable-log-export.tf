resource "aws_neptune_cluster" "bad_example" {
  storage_encrypted                   = true
  kms_key_arn                         = aws_kms_key.example.arn
}

resource "aws_neptune_cluster" "bad_example2" {
  enable_cloudwatch_logs_exports      = ["something"]
  
  storage_encrypted                   = true
  kms_key_arn                         = aws_kms_key.example.arn
}

resource "aws_neptune_cluster" "good_example" {
  enable_cloudwatch_logs_exports      = ["something", "audit"]

  storage_encrypted                   = true
  kms_key_arn                         = aws_kms_key.example.arn
}
