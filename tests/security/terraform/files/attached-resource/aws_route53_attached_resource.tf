resource "aws_alb" "fixed" {
  internal = true
  drop_invalid_header_fields = true
}

resource "aws_api_gateway_domain_name" "example" {
  certificate_arn = aws_acm_certificate_validation.example.certificate_arn
  domain_name     = "api.example.com"
  security_policy = "tls_1_2"
}

resource "aws_route53_record" "fail" {
  type    = "A"
}

resource "aws_route53_record" "fail2" {
  type    = "A"
  alias {
    evaluate_target_health = true
    name                   = aws_api_gateway_domain_name.example2.cloudfront_domain_name
    zone_id                = aws_api_gateway_domain_name.example2.cloudfront_zone_id
  }
}

resource "aws_route53_record" "pass" {
  type    = "A"
  records = [aws_alb.fixed.public_ip]
}

resource "aws_route53_record" "pass2" {
  name    = aws_api_gateway_domain_name.example.domain_name
  type    = "A"
  zone_id = aws_route53_zone.example.id

  alias {
    evaluate_target_health = true
    name                   = aws_api_gateway_domain_name.example.cloudfront_domain_name
    zone_id                = aws_api_gateway_domain_name.example.cloudfront_zone_id
  }
}
