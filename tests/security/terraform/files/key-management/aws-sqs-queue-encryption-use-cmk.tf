resource "aws_sqs_queue" "bad_example" {
}

resource "aws_sqs_queue" "bad_example" {
  kms_master_key_id = ""
}

resource "aws_sqs_queue" "good_example2" {
  kms_master_key_id = "/blah"
}
