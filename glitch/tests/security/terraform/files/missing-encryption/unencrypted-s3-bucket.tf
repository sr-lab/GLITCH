resource "aws_s3_bucket" "bad_example" {
  bucket = "bucket_bad"
  logging {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_replication_configuration" "bad_example" {
  bucket = aws_s3_bucket.bad_example.id
  rule {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "bad_example" {
  bucket = aws_s3_bucket.bad_example.id
  block_public_acls   = true
  ignore_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bad_example" {
  bucket = aws_s3_bucket.bad_example.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id =  aws_kms_key.mykey.arn
    }
  }
}

# ------------------------------------------------------------------------

resource "aws_s3_bucket" "bad_example2" {
  bucket = "bucket_bad"
  logging {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_replication_configuration" "bad_example2" {
  bucket = aws_s3_bucket.bad_example2.id
  rule {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "bad_example2" {
  bucket = aws_s3_bucket.bad_example2.id
  block_public_acls   = true
  ignore_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bad_example2" {
  bucket = aws_s3_bucket.bad_example2.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = ""
      kms_master_key_id =  aws_kms_key.mykey.arn
    }
  }
}

# ------------------------------------------------------------------------

resource "aws_s3_bucket" "good_example" {
  bucket = "bucket_good"
  logging {
  }
  versioning {
    enabled = true
  }
}

resource "aws_s3_bucket_replication_configuration" "good_example" {
  bucket = aws_s3_bucket.good_example.id
  rule {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "good_example" {
  bucket = aws_s3_bucket.good_example.id
  block_public_acls   = true
  ignore_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "good_example" {
  bucket = aws_s3_bucket.good_example.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.mykey.arn
    }
  }
}
