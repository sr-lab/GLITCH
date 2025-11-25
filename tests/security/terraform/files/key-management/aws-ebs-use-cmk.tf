resource "aws_ebs_volume" "bad_example" {
  encrypted = true
}

resource "aws_ebs_volume" "bad_example2" {
  encrypted = true
  kms_key_id = ""
}

resource "aws_ebs_volume" "good_example" {
  encrypted = true
  kms_key_id = aws_kms_key.ebs_encryption.arn
}
