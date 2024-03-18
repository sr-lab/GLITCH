resource "aws_s3_bucket" "source" {
  logging {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_replication_configuration" "bad_example" {
  bucket = aws_s3_bucket.source.id
}

resource "aws_s3_bucket_replication_configuration" "bad_example2" {
  bucket = aws_s3_bucket.source.id
  rule {
    status = "something"
  }
}

resource "aws_s3_bucket_replication_configuration" "good_example" {
  bucket = aws_s3_bucket.source.id
  rule {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.source.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = "something"
      sse_algorithm = "aes256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.source.id
  block_public_acls   = true
  ignore_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
}
