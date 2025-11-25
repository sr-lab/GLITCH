resource "aws_kinesis_stream" "bad_example" {
  encryption_type = "KMS"
}

resource "aws_kinesis_stream" "bad_example2" {
  encryption_type = "KMS"
  kms_key_id = ""
}

resource "aws_kinesis_stream" "good_example" {
  encryption_type = "KMS"
  kms_key_id = "my/special/key"
}
