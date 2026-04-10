resource "aws_s3_bucket_public_access_block" "bad_example" {
  bucket = aws_s3_bucket.example.id
  block_public_acls = true
  restrict_public_buckets = true
  ignore_public_acls = true
}

resource "aws_s3_bucket_public_access_block" "bad_example2" {
  bucket = aws_s3_bucket.example.id 
  block_public_acls = true
  block_public_policy = false
  restrict_public_buckets = true
  ignore_public_acls = true
}

resource "aws_s3_bucket_public_access_block" "good_example" {
  bucket = aws_s3_bucket.example.id 
  block_public_acls = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls = true
}

