resource "aws_dynamodb_table" "bad_example" {
  server_side_encryption {
    kms_key_arn = aws_kms_key.dynamo_db_kms.key_id
  }
}

resource "aws_dynamodb_table" "bad_example2" {
  server_side_encryption {
    enabled = false
    kms_key_arn = aws_kms_key.dynamo_db_kms.key_id
  }
}

resource "aws_dynamodb_table" "good_example" {
  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.dynamo_db_kms.key_id
  }
}
