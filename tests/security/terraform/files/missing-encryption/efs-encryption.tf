resource "aws_efs_file_system" "bad_example" {
}

resource "aws_efs_file_system" "bad_example2" {
  name       = "bar"
  encrypted  = false
  kms_key_id = ""
}

resource "aws_efs_file_system" "good_example" {
  name       = "bar"
  encrypted  = true
  kms_key_id = "my_kms_key"
}
