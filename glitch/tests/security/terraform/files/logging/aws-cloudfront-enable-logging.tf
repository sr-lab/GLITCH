resource "aws_cloudfront_distribution" "bad_example" {
  web_acl_id = "waf_id"
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
}

resource "aws_cloudfront_distribution" "bad_example2" {
  logging_config {
    bucket          = ""
  }

  web_acl_id = "waf_id"
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
}

resource "aws_cloudfront_distribution" "good_example" {
  logging_config {
    bucket          = "mylogs.s3.amazonaws.com"
  }

  web_acl_id = "waf_id"
  default_cache_behavior {
    viewer_protocol_policy = "redirect-to-https"
  }
  viewer_certificate {
    minimum_protocol_version = "tlsv1.2_2021"
  }
}
