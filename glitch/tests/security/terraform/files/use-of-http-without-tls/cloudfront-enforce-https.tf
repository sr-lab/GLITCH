resource "aws_cloudfront_distribution" "bad_example" {
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
  web_acl_id = "something"
  logging_config {
    bucket = "some_bucket"
  }
}

resource "aws_cloudfront_distribution" "bad_example2" {
  default_cache_behavior {
    viewer_protocol_policy = "allow-all"
  }

  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
  web_acl_id = "something"
  logging_config {
    bucket = "some_bucket"
  }
}

resource "aws_cloudfront_distribution" "good_example" {
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }

  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
  web_acl_id = "something"
  logging_config {
    bucket = "some_bucket"
  }
}
