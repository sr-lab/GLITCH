resource "aws_db_instance" "bad_example" {
  publicly_accessible = true
  kms_key_id = "something"
  performance_insights_enabled = true
  performance_insights_kms_key_id = "something"
  storage_encrypted = true
}

resource "aws_db_instance" "good_example" {
  publicly_accessible = false
  kms_key_id = "something"
  performance_insights_enabled = true
  performance_insights_kms_key_id = "something"
  storage_encrypted = true
}

resource "aws_rds_cluster_instance" "bad_example" {
  publicly_accessible = true
  performance_insights_enabled = true
  performance_insights_kms_key_id = "something"
  storage_encrypted = true
}

resource "aws_rds_cluster_instance" "good_example" {
  publicly_accessible = false
  performance_insights_kms_key_id = "something"
  performance_insights_enabled = true
  storage_encrypted = true
}

resource "aws_db_instance" "good_example2" {
  kms_key_id = "something"
  performance_insights_enabled = true
  performance_insights_kms_key_id = "something"
  storage_encrypted = true
}

resource "aws_rds_cluster_instance" "good_example2" {
  performance_insights_kms_key_id = "something"
  storage_encrypted = true
  performance_insights_enabled = true
}
