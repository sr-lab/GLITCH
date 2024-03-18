resource "aws_rds_cluster" "bad_example" {
  storage_encrypted = true
}

resource "aws_rds_cluster" "bad_example2" {
  storage_encrypted = true
  kms_key_id  = ""
}

resource "aws_rds_cluster" "good_example" {
  storage_encrypted = true
  kms_key_id  = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
}
