resource "aws_redshift_cluster" "bad_example" {
  kms_key_id         = aws_kms_key.redshift.key_id
}

resource "aws_redshift_cluster" "bad_example2" {
  encrypted          = false
  kms_key_id         = aws_kms_key.redshift.key_id
}

resource "aws_redshift_cluster" "good_example" {
  encrypted          = true
  kms_key_id         = aws_kms_key.redshift.key_id
}
