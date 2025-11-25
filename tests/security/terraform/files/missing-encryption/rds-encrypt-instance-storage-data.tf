resource "aws_db_instance" "bad_example" {
  kms_key_id  = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
  performance_insights_enabled = true
  performance_insights_kms_key_id = "something"
}

resource "aws_db_instance" "bad_example2" {
  storage_encrypted  = false
  performance_insights_kms_key_id = "something"
  performance_insights_enabled = true
  kms_key_id  = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
}

resource "aws_db_instance" "good_example" {
  storage_encrypted  = true
  performance_insights_kms_key_id = "something"
  performance_insights_enabled = true
  kms_key_id  = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
}
