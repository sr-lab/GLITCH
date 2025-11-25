resource "aws_redshift_cluster" "bad_example" {
  encrypted          = true
}

resource "aws_redshift_cluster" "bad_example2" {
  encrypted          = true
  kms_key_id         = ""
}

resource "aws_redshift_cluster" "good_example" {
  encrypted          = true
  kms_key_id         = aws_kms_key.redshift.key_id
}