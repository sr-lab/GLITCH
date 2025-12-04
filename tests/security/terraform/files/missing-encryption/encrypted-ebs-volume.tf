resource "aws_ebs_volume" "bad_example" {
  kms_key_id = "something"
}

resource "aws_ebs_volume" "bad_example2" {
  kms_key_id = "something"
  encrypted = false
}

resource "aws_ebs_volume" "good_example" {
  kms_key_id = "something"
  encrypted = true
}
