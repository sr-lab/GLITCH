resource "aws_cloudfront_distribution" "bad_example" {
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
  logging_config {
    bucket = "some_bucket"
  }
}

resource "aws_cloudfront_distribution" "bad_example2" {
  web_acl_id = ""

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
  logging_config {
    bucket = "some_bucket"
  }
}

resource "aws_cloudfront_distribution" "good_example" {
  web_acl_id = "waf_id"

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
  logging_config {
    bucket = "some_bucket"
  }
}
