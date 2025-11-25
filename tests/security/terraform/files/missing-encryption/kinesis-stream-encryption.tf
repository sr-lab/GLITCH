resource "aws_kinesis_stream" "bad_example" {
  kms_key_id = "my/special/key"
}

resource "aws_kinesis_stream" "bad_example2" {
  encryption_type = "NONE"
  kms_key_id = "my/special/key"
}

resource "aws_kinesis_stream" "good_example" {
  encryption_type = "KMS"
  kms_key_id = "my/special/key"
}