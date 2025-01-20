resource "aws_s3_bucket_server_side_encryption_configuration" "good_example" {
  bucket = aws_s3_bucket.good_example.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = "something"
      sse_algorithm = "aes256"
    }
  }
}