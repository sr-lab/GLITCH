resource "aws_kms_key" "bad_example" {
}

resource "aws_kms_key" "bad_example2" {
  enable_key_rotation = false
}

resource "aws_kms_key" "good_example" {
  enable_key_rotation = true
}
