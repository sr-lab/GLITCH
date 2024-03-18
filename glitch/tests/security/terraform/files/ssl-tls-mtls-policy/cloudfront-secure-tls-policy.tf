resource "aws_cloudfront_distribution" "bad_example" {
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  web_acl_id = "something"
  logging_config {
    bucket = "some_bucket"
  }
}

resource "aws_cloudfront_distribution" "bad_example2" {
  viewer_certificate {
    minimum_protocol_version = "TLSv1.0"
  }

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  web_acl_id = "something"
  logging_config {
    bucket = "some_bucket"
  }
}

resource "aws_cloudfront_distribution" "good_example" {
  viewer_certificate {
    minimum_protocol_version = "TLSv1.2_2021"
  }

  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  web_acl_id = "something"
  logging_config {
    bucket = "some_bucket"
  }
}
