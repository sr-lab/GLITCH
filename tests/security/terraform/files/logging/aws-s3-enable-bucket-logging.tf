resource "aws_s3_bucket" "example" {
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket" "example" {
  dynamic "logging" {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket" "example" {
  logging {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket" "example" {
  logging {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.example.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = "something"
      sse_algorithm = "aes256"
    }
  }
}

resource "aws_s3_bucket_replication_configuration" "example" {
  bucket = aws_s3_bucket.example.id
  rule {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.example.id
  block_public_acls   = true
  ignore_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
}
