resource "aws_rds_cluster_instance" "bad_example" {
  storage_encrypted = true
  performance_insights_kms_key_id = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
}

resource "aws_rds_cluster_instance" "bad_example2" {
  performance_insights_enabled = false
  
  storage_encrypted = true
  performance_insights_kms_key_id = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
}

resource "aws_rds_cluster_instance" "good_example" {
  performance_insights_enabled = true

  storage_encrypted = true
  performance_insights_kms_key_id = "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab"
}
