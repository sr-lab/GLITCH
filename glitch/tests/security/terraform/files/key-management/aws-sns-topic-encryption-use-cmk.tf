resource "aws_sns_topic" "bad_example" {
}

resource "aws_sns_topic" "bad_example" {
  kms_master_key_id = ""
}

resource "aws_sns_topic" "good_example2" {
  kms_master_key_id = "/blah"
}
